"""
CodeBERT-powered Code Clone Detector

Uses microsoft/codebert-base transformer to generate semantic embeddings
for each function in the codebase, then clusters similar functions using
cosine similarity to detect code clones.
"""

import os
import re
import ast
import logging
import hashlib
from typing import List, Dict, Any, Tuple

import torch
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# ── Lazy-load the model to avoid startup cost ──────────────────────────
_tokenizer = None
_model = None

def _load_codebert():
    """Load CodeBERT model and tokenizer on first use (~500 MB download)."""
    global _tokenizer, _model
    if _tokenizer is not None:
        return

    from transformers import AutoTokenizer, AutoModel

    logger.info("Loading microsoft/codebert-base … (first run downloads ~500 MB)")
    _tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
    _model = AutoModel.from_pretrained("microsoft/codebert-base")
    _model.eval()
    logger.info("CodeBERT loaded successfully.")


# ── Function extraction ────────────────────────────────────────────────

def _extract_python_functions(filepath: str, source: str) -> List[Dict[str, Any]]:
    """Extract functions from a Python file using the ast module."""
    functions = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return functions

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start_line = node.lineno
            end_line = node.end_lineno or start_line
            lines = source.splitlines()[start_line - 1 : end_line]
            code = "\n".join(lines)
            if len(code.strip()) < 30:          # skip trivial one-liners
                continue
            functions.append({
                "file": filepath,
                "name": node.name,
                "start_line": start_line,
                "end_line": end_line,
                "code": code,
            })
    return functions


def _extract_js_ts_functions(filepath: str, source: str) -> List[Dict[str, Any]]:
    """
    Extract functions from JS/TS files via regex.
    Handles:  function foo()  |  const foo = () =>  |  async function foo()
    """
    functions = []
    # Match function declarations and arrow functions assigned to const/let
    patterns = [
        r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*\{",
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*(?::\s*\w+)?\s*=>\s*\{",
    ]

    lines = source.splitlines()
    for pattern in patterns:
        for match in re.finditer(pattern, source):
            name = match.group(1)
            start_pos = match.start()
            start_line = source[:start_pos].count("\n") + 1

            # Walk forward counting braces to find end of function
            brace_count = 0
            end_line = start_line
            started = False
            for i in range(start_line - 1, len(lines)):
                for ch in lines[i]:
                    if ch == "{":
                        brace_count += 1
                        started = True
                    elif ch == "}":
                        brace_count -= 1
                if started and brace_count == 0:
                    end_line = i + 1
                    break

            code = "\n".join(lines[start_line - 1 : end_line])
            if len(code.strip()) < 30:
                continue
            functions.append({
                "file": filepath,
                "name": name,
                "start_line": start_line,
                "end_line": end_line,
                "code": code,
            })
    return functions


EXTENSION_MAP = {
    ".py": _extract_python_functions,
    ".js": _extract_js_ts_functions,
    ".ts": _extract_js_ts_functions,
    ".tsx": _extract_js_ts_functions,
    ".jsx": _extract_js_ts_functions,
}


def extract_functions_from_directory(root_dir: str) -> List[Dict[str, Any]]:
    """Walk a directory tree and extract all functions."""
    all_functions: List[Dict[str, Any]] = []
    for dirpath, _, filenames in os.walk(root_dir):
        # Skip common non-source dirs
        if any(skip in dirpath for skip in ["node_modules", ".git", "__pycache__", ".next", "venv"]):
            continue
        for fname in filenames:
            ext = os.path.splitext(fname)[1]
            extractor = EXTENSION_MAP.get(ext)
            if not extractor:
                continue
            fullpath = os.path.join(dirpath, fname)
            try:
                with open(fullpath, "r", encoding="utf-8", errors="ignore") as f:
                    source = f.read()
                rel_path = os.path.relpath(fullpath, root_dir).replace("\\", "/")
                all_functions.extend(extractor(rel_path, source))
            except Exception as e:
                logger.warning(f"Skipping {fullpath}: {e}")
    return all_functions


# ── Embedding generation ───────────────────────────────────────────────

def _embed_functions(functions: List[Dict[str, Any]]) -> np.ndarray:
    """
    Generate CodeBERT embeddings for a list of functions.
    Returns an (N, 768) numpy array.
    """
    _load_codebert()

    embeddings = []
    for fn in functions:
        code = fn["code"]
        # Truncate to CodeBERT's max 512 tokens
        inputs = _tokenizer(
            code,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding="max_length",
        )
        with torch.no_grad():
            outputs = _model(**inputs)
        # Use [CLS] token embedding as the function representation
        cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze().numpy()
        embeddings.append(cls_embedding)

    return np.array(embeddings)


# ── Clone detection ────────────────────────────────────────────────────

def detect_clones(
    functions: List[Dict[str, Any]],
    threshold: float = 0.85,
) -> List[Dict[str, Any]]:
    """
    Given a list of extracted functions, compute pairwise cosine similarity
    using CodeBERT embeddings and cluster clones above the threshold.
    """
    if len(functions) < 2:
        return []

    logger.info(f"Embedding {len(functions)} functions with CodeBERT …")
    embeddings = _embed_functions(functions)

    # Pairwise cosine similarity (N×N matrix)
    sim_matrix = cosine_similarity(embeddings)

    # Find pairs above threshold (upper triangle only to avoid duplicates)
    n = len(functions)
    clone_pairs: List[Tuple[int, int, float]] = []
    for i in range(n):
        for j in range(i + 1, n):
            score = float(sim_matrix[i][j])
            if score >= threshold:
                # Skip if same file and overlapping lines (same function)
                if functions[i]["file"] == functions[j]["file"] and \
                   functions[i]["start_line"] == functions[j]["start_line"]:
                    continue
                clone_pairs.append((i, j, score))

    # Group pairs into clusters using Union-Find
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i, j, _ in clone_pairs:
        union(i, j)

    # Build cluster map
    clusters: Dict[int, List[Tuple[int, float]]] = {}
    for i, j, score in clone_pairs:
        root = find(i)
        if root not in clusters:
            clusters[root] = set()
        clusters[root].add(i)
        clusters[root].add(j)

    # Format output
    result = []
    for cluster_idx, (root, member_indices) in enumerate(clusters.items()):
        members = sorted(member_indices)
        # Average similarity across cluster members
        sims = []
        for a in members:
            for b in members:
                if a < b:
                    sims.append(float(sim_matrix[a][b]))
        avg_sim = np.mean(sims) if sims else 0.0

        instances = []
        for idx in members:
            fn = functions[idx]
            instances.append({
                "file": fn["file"],
                "name": fn["name"],
                "start_line": fn["start_line"],
                "end_line": fn["end_line"],
                "code": fn["code"][:500],  # Truncate for API response
            })

        result.append({
            "cluster_id": f"cluster_{cluster_idx}",
            "similarity_score": round(avg_sim, 3),
            "instances": instances,
            "recommendation": _generate_recommendation(instances),
        })

    # Sort by similarity descending
    result.sort(key=lambda c: c["similarity_score"], reverse=True)
    logger.info(f"Found {len(result)} clone clusters.")
    return result


def _generate_recommendation(instances: List[Dict]) -> str:
    """Generate a human-readable refactoring recommendation."""
    files = set(inst["file"] for inst in instances)
    names = [inst["name"] for inst in instances]
    if len(files) > 1:
        return f"Functions {', '.join(names)} are semantically similar across {len(files)} files. Extract to a shared utility module."
    else:
        return f"Functions {', '.join(names)} in the same file are near-duplicates. Consolidate into a single function."


# ── Public API ─────────────────────────────────────────────────────────

def scan_repository(repo_path: str, threshold: float = 0.85) -> List[Dict[str, Any]]:
    """
    Full pipeline: extract functions → embed with CodeBERT → detect clones.
    """
    logger.info(f"Scanning repository at {repo_path} …")
    functions = extract_functions_from_directory(repo_path)
    logger.info(f"Extracted {len(functions)} functions from {repo_path}")

    if len(functions) < 2:
        return []

    return detect_clones(functions, threshold=threshold)

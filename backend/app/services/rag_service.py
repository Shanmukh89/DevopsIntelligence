"""
RAG (Retrieval-Augmented Generation) Service for Codebase Q&A

Pipeline:
  1. Index: Chunk code files by function boundaries → embed with OpenAI
     text-embedding-3-small → store in Supabase pgvector
  2. Query: Embed the question → cosine similarity search in pgvector →
     retrieve top 5 chunks → send to GPT-4o with citation instructions
"""

import os
import re
import ast
import json
import logging
from typing import List, Dict, Any, Optional

import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Code Chunking ──────────────────────────────────────────────────────

def _chunk_python_file(filepath: str, source: str) -> List[Dict[str, Any]]:
    """Split a Python file into semantic chunks (functions/classes)."""
    chunks = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Fallback: treat entire file as one chunk
        return [{
            "file": filepath,
            "start_line": 1,
            "end_line": len(source.splitlines()),
            "content": source[:2000],
            "type": "file",
        }]

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = node.lineno
            end = node.end_lineno or start
            lines = source.splitlines()[start - 1 : end]
            content = "\n".join(lines)
            if len(content.strip()) < 20:
                continue
            chunks.append({
                "file": filepath,
                "start_line": start,
                "end_line": end,
                "content": content[:2000],
                "type": "class" if isinstance(node, ast.ClassDef) else "function",
                "name": node.name,
            })

    # If no functions/classes found, chunk the file in ~300-line blocks
    if not chunks:
        lines = source.splitlines()
        for i in range(0, len(lines), 300):
            block = "\n".join(lines[i : i + 300])
            if block.strip():
                chunks.append({
                    "file": filepath,
                    "start_line": i + 1,
                    "end_line": min(i + 300, len(lines)),
                    "content": block[:2000],
                    "type": "block",
                })
    return chunks


def _chunk_js_ts_file(filepath: str, source: str) -> List[Dict[str, Any]]:
    """Split JS/TS files into chunks using regex function detection + fallback blocks."""
    chunks = []
    lines = source.splitlines()

    # Try to extract functions
    patterns = [
        r"(?:export\s+)?(?:async\s+)?function\s+(\w+)",
        r"(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*(?:async\s+)?\(",
        r"(?:export\s+)?class\s+(\w+)",
    ]

    found = False
    for pattern in patterns:
        for match in re.finditer(pattern, source):
            name = match.group(1)
            start_pos = match.start()
            start_line = source[:start_pos].count("\n") + 1

            # Find the end by brace counting
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

            content = "\n".join(lines[start_line - 1 : end_line])
            if len(content.strip()) > 20:
                chunks.append({
                    "file": filepath,
                    "start_line": start_line,
                    "end_line": end_line,
                    "content": content[:2000],
                    "type": "function",
                    "name": name,
                })
                found = True

    if not found:
        for i in range(0, len(lines), 300):
            block = "\n".join(lines[i : i + 300])
            if block.strip():
                chunks.append({
                    "file": filepath,
                    "start_line": i + 1,
                    "end_line": min(i + 300, len(lines)),
                    "content": block[:2000],
                    "type": "block",
                })
    return chunks


CHUNKERS = {
    ".py": _chunk_python_file,
    ".js": _chunk_js_ts_file,
    ".ts": _chunk_js_ts_file,
    ".tsx": _chunk_js_ts_file,
    ".jsx": _chunk_js_ts_file,
}


def chunk_repository(repo_path: str) -> List[Dict[str, Any]]:
    """Walk a repo and chunk all source files."""
    all_chunks = []
    for dirpath, _, filenames in os.walk(repo_path):
        if any(skip in dirpath for skip in ["node_modules", ".git", "__pycache__", ".next", "venv"]):
            continue
        for fname in filenames:
            ext = os.path.splitext(fname)[1]
            chunker = CHUNKERS.get(ext)
            if not chunker:
                continue
            fullpath = os.path.join(dirpath, fname)
            try:
                with open(fullpath, "r", encoding="utf-8", errors="ignore") as f:
                    source = f.read()
                rel_path = os.path.relpath(fullpath, repo_path).replace("\\", "/")
                all_chunks.extend(chunker(rel_path, source))
            except Exception as e:
                logger.warning(f"Skipping {fullpath}: {e}")
    return all_chunks


# ── Embedding via OpenAI ───────────────────────────────────────────────

def _get_embeddings(texts: List[str]) -> List[List[float]]:
    """Call OpenAI text-embedding-3-small to produce embeddings."""
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY required for RAG embeddings")

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    # OpenAI embedding API supports batching up to 2048 inputs
    all_embeddings = []
    batch_size = 2048
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        payload = {
            "model": "text-embedding-3-small",
            "input": batch,
        }
        resp = httpx.post(
            "https://api.openai.com/v1/embeddings",
            headers=headers,
            json=payload,
            timeout=120.0,
        )
        resp.raise_for_status()
        data = resp.json()
        batch_embeddings = [item["embedding"] for item in data["data"]]
        all_embeddings.extend(batch_embeddings)

    return all_embeddings


# ── In-Memory Vector Store (fallback when pgvector is unavailable) ─────

_indices: Dict[str, Dict[str, Any]] = {}

def _clone_and_index_github_repo(repo_full_name: str) -> bool:
    import tempfile
    import zipfile
    import urllib.request
    import urllib.error
    
    logger.info(f"Auto-downloading and indexing GitHub repository: {repo_full_name}")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            token = settings.GITHUB_TOKEN
            # Use the GitHub API to get the default branch zipball
            api_url = f"https://api.github.com/repos/{repo_full_name}/zipball"
            
            req = urllib.request.Request(api_url)
            if token:
                req.add_header("Authorization", f"Bearer {token}")
            req.add_header("Accept", "application/vnd.github.v3+json")
            req.add_header("User-Agent", "DevopsIntelligence-App")
            
            zip_path = os.path.join(tmpdir, "repo.zip")
            try:
                with urllib.request.urlopen(req) as response, open(zip_path, "wb") as out_file:
                    out_file.write(response.read())
            except urllib.error.HTTPError as e:
                logger.error(f"GitHub API Error downloading repo: {e}")
                return False
                
            # Extract the zip file
            extract_dir = os.path.join(tmpdir, "extracted")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # The root of the zip usually contains a single folder like Owner-Repo-sha
            # chunk_repository will naturally walk down through it
            chunks = chunk_repository(extract_dir)
            if not chunks:
                logger.warning(f"No chunks found in {repo_full_name}")
                return False
                
            texts = []
            for chunk in chunks:
                text = f"File: {chunk['file']}\nType: {chunk['type']}\n"
                if chunk.get("name"):
                    text += f"Name: {chunk['name']}\n"
                text += f"Lines: {chunk['start_line']}-{chunk['end_line']}\n\n{chunk['content']}"
                texts.append(text[:8000])

            embeddings = _get_embeddings(texts)
            import numpy as np
            vectors = np.array(embeddings, dtype=np.float32)
            
            _indices[repo_full_name] = {"index": chunks, "vectors": vectors}
            logger.info(f"Successfully indexed {repo_full_name}")
            return True
    except Exception as e:
        logger.error(f"Failed to download and index {repo_full_name}: {e}")
        return False

def index_repository(repo_path: str) -> Dict[str, Any]:
    """
    Index a repository: chunk → embed → store in memory.
    In production, these would go into Supabase pgvector.
    """
    global _indices

    logger.info(f"Indexing repository at {repo_path} for RAG …")
    chunks = chunk_repository(repo_path)
    logger.info(f"Extracted {len(chunks)} code chunks")

    if not chunks:
        return {"status": "no_chunks_found", "chunks": 0}

    # Build text representations for embedding
    texts = []
    for chunk in chunks:
        # Combine metadata with content for richer embeddings
        text = f"File: {chunk['file']}\nType: {chunk['type']}\n"
        if chunk.get("name"):
            text += f"Name: {chunk['name']}\n"
        text += f"Lines: {chunk['start_line']}-{chunk['end_line']}\n\n{chunk['content']}"
        texts.append(text[:8000])  # OpenAI limit per input

    logger.info(f"Generating embeddings for {len(texts)} chunks …")
    embeddings = _get_embeddings(texts)

    import numpy as np
    vectors = np.array(embeddings, dtype=np.float32)
    _indices[repo_path] = {"index": chunks, "vectors": vectors}

    logger.info(f"RAG index built: {len(chunks)} chunks, {vectors.shape[1]}-dim embeddings")
    return {"status": "indexed", "chunks": len(chunks), "dimensions": vectors.shape[1]}


def answer_question(question: str, repo_path: Optional[str] = None, repo_full_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Answer a codebase question using RAG:
      1. Embed the question
      2. Similarity search against indexed chunks
      3. Feed top chunks + question to GPT-4o
    """
    global _indices

    if not settings.OPENAI_API_KEY:
        return {
            "answer": "OpenAI API key is required for code Q&A.",
            "sources": [],
        }

    # Determine which key to use for the index lookup
    index_key = repo_full_name if repo_full_name else repo_path

    if index_key and index_key not in _indices:
        if repo_full_name:
            _clone_and_index_github_repo(repo_full_name)
        elif repo_path and os.path.exists(repo_path):
            index_repository(repo_path)
    
    # If no index is still available, try default fallback
    if not index_key or index_key not in _indices:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        if project_root not in _indices and os.path.exists(project_root):
             index_repository(project_root)
        index_key = project_root

    # Check if we successfully have vectors to query
    if index_key not in _indices or _indices[index_key]["vectors"] is None or len(_indices[index_key]["index"]) == 0:
        return {
            "answer": "No code has been indexed yet. Please run indexing first.",
            "sources": [],
        }

    # Embed the question
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity

    q_embedding = np.array(_get_embeddings([question])[0], dtype=np.float32).reshape(1, -1)

    # Cosine similarity search
    _vectors = _indices[index_key]["vectors"]
    _index = _indices[index_key]["index"]
    similarities = cosine_similarity(q_embedding, _vectors)[0]
    top_k = 5
    top_indices = np.argsort(similarities)[-top_k:][::-1]

    # Retrieve top chunks
    retrieved_chunks = []
    for idx in top_indices:
        chunk = _index[idx]
        retrieved_chunks.append({
            "file": chunk["file"],
            "lines": f"{chunk['start_line']}-{chunk['end_line']}",
            "content": chunk["content"],
            "similarity": round(float(similarities[idx]), 3),
        })

    # Build prompt for GPT-4o
    context = ""
    for i, chunk in enumerate(retrieved_chunks):
        context += f"\n--- Source {i+1}: {chunk['file']} (L{chunk['lines']}) ---\n"
        context += chunk["content"]
        context += "\n"

    prompt = f"""You are an expert software engineer assistant. Answer the user's question
about the codebase using ONLY the provided code snippets. Be specific and cite 
the exact file path and line numbers for every claim you make.

If the provided code does not contain enough information to answer, say so honestly.

Format your citations inline like: `filename.py` (lines 10-25)

CODE CONTEXT:
{context}

USER QUESTION: {question}
"""

    # Call GPT-4o
    try:
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60.0,
        )
        resp.raise_for_status()
        answer = resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"GPT-4o call failed: {e}")
        answer = "Failed to generate answer from the LLM."

    # Build sources list for the citation panel
    sources = [
        {
            "file": c["file"],
            "lines": c["lines"],
            "snippet": c["content"][:500],
            "similarity": c["similarity"],
        }
        for c in retrieved_chunks
    ]

    return {
        "answer": answer,
        "sources": sources,
    }

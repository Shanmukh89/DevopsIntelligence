import logging
import json
from typing import List, Dict, Any
from app.core.config import settings

# Initialize OpenAI client 
try:
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
except ImportError:
    client = None

logger = logging.getLogger(__name__)

def evaluate_code_diff(diff_text: str) -> List[Dict[str, Any]]:
    """
    AI code review of a diff using OpenAI.
    """
    if not client or not settings.OPENAI_API_KEY:
        logger.warning("No OPENAI_API_KEY set. Skipping real AI Code Review and returning mock.")
        return [
            {
                "severity": "info",
                "line_number": 1,
                "description": "Mock AI review: consider checking best practices here.",
                "suggestion": "Follow established typing guidelines."
            }
        ]

    prompt = f"""
    You are an expert code reviewer with 10 years of experience. 
    Review the following code changes and identify:
    - Security vulnerabilities (label: SECURITY)
    - Potential bugs or edge cases (label: BUG)  
    - Performance issues (label: PERFORMANCE)
    - Style or maintainability issues (label: STYLE)

    For each issue, specify the exact line number, severity (critical/warning/info), 
    a one-sentence description, and a concrete fix suggestion.

    Format your response EXACTLY as a JSON array of objects with keys: severity, line_number, description, suggestion.
    Do NOT wrap the JSON in Markdown codeblocks.

    Code diff:
    {diff_text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt}]
        )
        content = response.choices[0].message.content.strip()
        # Clean up markdown block if present
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
        
        return json.loads(content)
    except Exception as e:
        logger.error(f"Error during AI review: {e}")
        return []

def explain_ci_failure(log_text: str) -> Dict[str, str]:
    """
    Runs root cause analysis on a CI failure log and returns a reason and a fix.
    """
    if not client or not settings.OPENAI_API_KEY:
        logger.warning("No OPENAI_API_KEY set. Skipping real CI Failure explanation.")
        return {
            "root_cause": "The build appears to have failed due to an unknown error.",
            "suggestion": "Check the build logs for specific syntax tracking issues."
        }

    prompt = f"""
    The following is the end of a failed CI/CD build log. 

    In 2-3 plain English sentences, explain what caused the failure — 
    do not repeat the error text verbatim, translate it into human language.

    Then provide one specific, actionable step to fix it. Be direct.

    Format output STRICTLY as a JSON object with two keys: "root_cause" and "suggestion".
    No markdown code blocks.

    Log:
    {log_text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt}]
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()

        return json.loads(content)
    except Exception as e:
        logger.error(f"Error generating CI explanation: {e}")
        return {"root_cause": "Failed to analyze error", "suggestion": "Check logs directly."}

def optimize_sql_query(query: str, explain_output: str) -> Dict[str, Any]:
    """
    Analyzes an EXPLAIN output and original query to suggest optimizations.
    """
    if not client or not settings.OPENAI_API_KEY:
        return {
            "rewritten_query": query,
            "explanation": ["Add an index on the filtered column to speed up scans.", "Use specific column selects instead of SELECT *."],
            "indexes": ["CREATE INDEX idx_mock ON my_table(my_column);"]
        }

    prompt = f"""
    You are a PostgreSQL performance expert. The following SQL query runs slowly.

    Original query:
    {query}

    EXPLAIN ANALYZE output:
    {explain_output}

    Provide:
    1. A rewritten version of the query that performs better
    2. A list of string explanations of every change you made
    3. Any CREATE INDEX statements

    Return output strictly as JSON with keys: "rewritten_query" (string), "explanation" (list of strings), "indexes" (list of strings).
    No markdown wrap.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt}]
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()

        return json.loads(content)
    except Exception as e:
        logger.error(f"Error analyzing SQL: {e}")
        return {"rewritten_query": query, "explanation": [], "indexes": []}

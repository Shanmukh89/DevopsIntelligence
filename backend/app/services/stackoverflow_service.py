import httpx
import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

STACK_EXCHANGE_API_URL = "https://api.stackexchange.com/2.3"

def extract_searchable_query(error_text: str) -> str:
    """
    Cleans up a raw error log trace to extract a searchable query.
    Takes the last non-empty line or the most prominent exception.
    """
    lines = [line.strip() for line in error_text.splitlines() if line.strip()]
    if not lines:
        return "Unknown error"
    
    # Simple heuristic: look for lines containing "Error:" or "Exception:"
    for line in reversed(lines):
        if "error" in line.lower() or "exception" in line.lower():
            # Remove timestamps or file paths if possible (basic cleanup)
            clean = re.sub(r'^[0-9T:.\-Z\s]+', '', line)
            clean = re.sub(r'\/[\/\w\.\-]+\.(py|js|ts|go|java)\:\d+', '', clean)
            return clean.strip()
    
    return lines[-1]

def find_solutions(error_text: str, tags: str = "") -> List[Dict[str, Any]]:
    """
    Searches StackOverflow for the closest matching error.
    """
    query = extract_searchable_query(error_text)
    logger.info(f"Searching StackOverflow for: {query}")
    
    params = {
        "order": "desc",
        "sort": "votes",
        "q": query,
        "site": "stackoverflow",
        "filter": "!9_bDDxJY5", # This filter includes body_markdown
        "pagesize": 3
    }
    
    if tags:
        params["tagged"] = tags
        
    try:
        response = httpx.get(f"{STACK_EXCHANGE_API_URL}/search/advanced", params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get("items", []):
            if item.get("is_answered") and item.get("score", 0) > 0:
                results.append({
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "score": item.get("score"),
                    "is_answered": item.get("is_answered")
                })
        
        return results
    except Exception as e:
        logger.error(f"StackOverflow API request failed: {e}")
        return []

import os
import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services import ai_service

router = APIRouter(prefix="/features", tags=["Features"])
logger = logging.getLogger(__name__)

# ── Request Models ─────────────────────────────────────────────────────

class SqlOptimizeRequest(BaseModel):
    query: str

class QARequest(BaseModel):
    question: str
    repository_id: str

class CloneDetectorRequest(BaseModel):
    repo_path: Optional[str] = None
    threshold: float = 0.85

class LogAnomalyRequest(BaseModel):
    retrain: bool = False


# ── SQL Optimizer ──────────────────────────────────────────────────────

@router.post("/sql-optimizer")
async def optimize_sql(req: SqlOptimizeRequest):
    """
    Accepts raw SQL, generates a mock EXPLAIN ANALYZE plan, and asks AI to optimize it.
    """
    mock_explain = r"""
    ->  Seq Scan on users  (cost=0.00..25.88 rows=5 width=95) (actual time=0.015..0.024 rows=3 loops=1)
          Filter: (status = 'active')
          Rows Removed by Filter: 997
    Planning Time: 0.124 ms
    Execution Time: 0.057 ms
    """
    result = ai_service.optimize_sql_query(req.query, mock_explain)
    return result


# ── Code Q&A (RAG Pipeline) ───────────────────────────────────────────

@router.post("/code-qa")
async def codebase_qa(req: QARequest):
    """
    Answers codebase questions using RAG:
    Chunks code → embeds with OpenAI → similarity search → GPT-4o answer.
    """
    from app.services import rag_service

    # Auto-detect the project root or use the provided custom path
    if req.repository_id and req.repository_id.lower() != "default":
        repo_path = req.repository_id
    else:
        repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    try:
        result = rag_service.answer_question(req.question, repo_path=repo_path)
        return result
    except Exception as e:
        logger.error(f"RAG Q&A failed: {e}")
        return {
            "answer": f"Error: {str(e)}",
            "sources": [],
        }


# ── Code Q&A Index Trigger ─────────────────────────────────────────────

@router.post("/code-qa/index")
async def index_codebase():
    """Manually trigger codebase indexing for RAG."""
    from app.services import rag_service

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    try:
        result = rag_service.index_repository(project_root)
        return result
    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        return {"status": "error", "detail": str(e)}


# ── Clone Detector (CodeBERT) ──────────────────────────────────────────

@router.post("/clone-detector")
async def detect_code_clones(req: CloneDetectorRequest):
    """
    Scans a repository for code clones using CodeBERT embeddings
    and cosine similarity clustering.
    """
    from app.services import clone_detector_ml

    # Default to the project root
    repo_path = req.repo_path
    if not repo_path:
        repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    try:
        clones = clone_detector_ml.scan_repository(repo_path, threshold=req.threshold)
        return {"clones": clones}
    except Exception as e:
        logger.error(f"Clone detection failed: {e}")
        return {"clones": [], "error": str(e)}


# Keep GET as a convenience alias that scans the project root
@router.get("/clone-detector")
async def get_code_clones():
    """GET convenience alias — scans the project root with default threshold."""
    from app.services import clone_detector_ml

    repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    try:
        clones = clone_detector_ml.scan_repository(repo_path, threshold=0.85)
        return {"clones": clones}
    except Exception as e:
        logger.error(f"Clone detection failed: {e}")
        return {"clones": [], "error": str(e)}


# ── Log Anomaly Detector (LSTM Autoencoder) ────────────────────────────

@router.post("/log-anomaly-detect")
async def detect_log_anomalies(req: LogAnomalyRequest):
    """
    Trains an LSTM Autoencoder on synthetic normal log data (if needed),
    then runs inference on test data with injected anomalies.
    Returns a timeline with flagged anomaly windows.
    """
    from app.services import log_anomaly_detector

    try:
        if req.retrain:
            log_anomaly_detector._trained_model = None  # Force retrain

        result = log_anomaly_detector.detect_anomalies()
        return result
    except Exception as e:
        logger.error(f"Log anomaly detection failed: {e}")
        return {"error": str(e)}

import hmac
import hashlib
import json
from fastapi import APIRouter, Request, Header, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.services import github_service

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

def verify_github_signature(payload_body: bytes, signature_header: str) -> bool:
    """Verify that the webhook payload was sent from GitHub using our secret."""
    if not settings.GITHUB_WEBHOOK_SECRET:
        # If no secret is configured, bypass signature checking (only for local dev)
        return True
        
    if not signature_header:
        return False
        
    hash_object = hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256,
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    return hmac.compare_digest(expected_signature, signature_header)


@router.post("/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Receive webhook events from GitHub App.
    """
    # 1. Verify signature
    payload_body = await request.body()
    if not verify_github_signature(payload_body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid GitHub signature")

    try:
        payload = json.loads(payload_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # 2. Dispatch events
    if x_github_event == "pull_request":
        # Process Pull Request Events (Opened, Synchronize)
        action = payload.get("action")
        if action in ["opened", "synchronize", "reopened"]:
            background_tasks.add_task(github_service.process_pull_request_event, db, payload)
            
    elif x_github_event == "workflow_run":
        # Process CI Build Failures
        action = payload.get("action")
        if action == "completed":
            workflow_run = payload.get("workflow_run", {})
            if workflow_run.get("conclusion") == "failure":
                background_tasks.add_task(github_service.process_workflow_failure, db, payload)
                
    elif x_github_event == "ping":
        return {"msg": "pong"}
        
    return {"status": "accepted", "event": x_github_event}

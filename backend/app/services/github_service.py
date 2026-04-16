import logging
import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session
from github import Github, GithubIntegration

from app.core.config import settings
from app.services import ai_service, slack_service
from app.services import stackoverflow_service

logger = logging.getLogger(__name__)

def get_github_installation_client(installation_id: int):
    """
    Returns an authenticated Github client for a specific installation.
    """
    if not settings.GITHUB_APP_ID or not settings.GITHUB_APP_PRIVATE_KEY_PATH:
        return Github(settings.GITHUB_TOKEN) # Fallback to personal token if app not configured
        
    try:
        with open(settings.GITHUB_APP_PRIVATE_KEY_PATH, 'r') as f:
            private_key = f.read()
        integration = GithubIntegration(
            integration_id=int(settings.GITHUB_APP_ID),
            private_key=private_key
        )
        access_token = integration.get_access_token(installation_id).token
        return Github(access_token)
    except Exception as e:
        logger.error(f"Failed to authenticate github app: {e}")
        return Github(settings.GITHUB_TOKEN)

def process_pull_request_event(db: Session, payload: dict):
    """
    Background task to handle an opened or updated PR:
    1. Fetch diff from GitHub API
    2. Pass diff to AI Service for review
    3. Post review comment back to GitHub
    4. Save review results to database
    """
    pr_data = payload.get("pull_request", {})
    repo_data = payload.get("repository", {})
    installation_id = payload.get("installation", {}).get("id")
    action = payload.get("action")
    
    repo_name = repo_data.get("full_name")
    pr_number = pr_data.get("number")
    
    logger.info(f"Processing PR {action}: {repo_name}#{pr_number}")
    
    try:
        gh = get_github_installation_client(installation_id) if installation_id else Github(settings.GITHUB_TOKEN)
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        # Fetch diff via the public diff_url
        diff_url = pr_data.get("diff_url")
        if not diff_url:
            logger.warning("No diff_url found")
            return
        
        # Use synchronous httpx for background task context
        diff_resp = httpx.get(diff_url, follow_redirects=True, timeout=30.0)
        diff_text = diff_resp.text
        
        if not diff_text or len(diff_text) > 100000:
            logger.warning("Diff too large or empty to process")
            return
            
        reviews = ai_service.evaluate_code_diff(diff_text)
        logger.info(f"Got {len(reviews)} issues from AI. Posting to PR.")
        
        issues_count = len(reviews)
        severity = "low"
        
        for issue in reviews:
            if issue.get("severity") == "critical":
                severity = "critical"
            elif issue.get("severity") == "warning" and severity != "critical":
                severity = "high"
                
            comment_body = f"**{issue.get('severity', 'info').upper()} Issue Detected (Line {issue.get('line_number', '?')}):**\n"
            comment_body += f"{issue.get('description', '')}\n\n*Suggestion:* {issue.get('suggestion', '')}"
            
            # Post comment to the PR
            pr.create_issue_comment(comment_body)
            
        # Update DB with review results
        try:
            db.execute(
                text(
                    "INSERT INTO pr_reviews (pull_request_id, issues_found, severity, summary_text) "
                    "SELECT pr.id, :issues, :severity, :summary "
                    "FROM pull_requests pr WHERE pr.github_pr_id = :gh_pr_id"
                ),
                {"issues": issues_count, "severity": severity, "summary": f"Found {issues_count} issues.", "gh_pr_id": pr_data.get("id")}
            )
            db.commit()
        except Exception as e:
            logger.error(f"Failed to save PR review to DB: {e}")
            db.rollback()

    except Exception as e:
        logger.error(f"Error processing PR: {e}")

def process_workflow_failure(db: Session, payload: dict):
    """
    Background task to handle a failed CI workflow:
    1. Download logs via GitHub API
    2. Pass logs to AI Service for root cause analysis
    3. Search StackOverflow for solutions
    4. Post explanation to Slack
    """
    workflow_run = payload.get("workflow_run", {})
    repo_data = payload.get("repository", {})
    installation_id = payload.get("installation", {}).get("id")
    repo_name = repo_data.get("full_name")
    
    logger.info(f"Processing Workflow Failure: {repo_name} run {workflow_run.get('id')}")
    
    try:
        gh = get_github_installation_client(installation_id) if installation_id else Github(settings.GITHUB_TOKEN)
        repo = gh.get_repo(repo_name)
        
        # Get failed job logs via the GitHub API
        jobs_url = workflow_run.get("jobs_url")
        
        headers = {"Accept": "application/vnd.github+json"}
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
            
        jobs_resp = httpx.get(jobs_url, headers=headers, timeout=15.0).json()
        failed_jobs = [j for j in jobs_resp.get("jobs", []) if j.get("conclusion") == "failure"]
        
        log_text = "Unknown error in build"
        if failed_jobs:
            log_url = failed_jobs[0].get("url") + "/logs"
            try:
                log_resp = httpx.get(log_url, headers=headers, timeout=15.0)
                if log_resp.status_code == 200:
                    lines = log_resp.text.splitlines()
                    # Take last 150 lines
                    log_text = "\n".join(lines[-150:])
            except Exception:
                pass
                
        explanation = ai_service.explain_ci_failure(log_text)
        
        # Extract search snippet and hit SO
        solutions = stackoverflow_service.find_solutions(log_text)
        
        slack_service.notify_ci_failure(
            repository_name=repo_name,
            build_url=workflow_run.get("html_url"),
            explanation=explanation,
            so_solutions=solutions
        )
        
    except Exception as e:
        logger.error(f"Error processing workflow failure: {e}")

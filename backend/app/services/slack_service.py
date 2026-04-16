import logging
from typing import Dict, Any, List
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Slack Client
slack_client = WebClient(token=settings.SLACK_BOT_TOKEN) if settings.SLACK_BOT_TOKEN else None
SLACK_CHANNEL = "#builds"

def notify_ci_failure(repository_name: str, build_url: str, explanation: Dict[str, str], so_solutions: List[Dict[str, Any]] = None):
    """
    Sends a structured Block Kit message to Slack about a CI failure,
    including the AI explanation and potential StackOverflow fixes.
    """
    if not slack_client or not settings.SLACK_BOT_TOKEN:
        logger.warning(f"No SLACK_BOT_TOKEN set. Cannot send notification for {repository_name}. Message details: {explanation}")
        return False
        
    logger.info(f"Sending slack notification for {repository_name} failure...")
    
    # Build Block Kit message
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🚨 CI Build Failed: {repository_name}",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Root Cause (AI Analysis):*\n{explanation.get('root_cause', 'Unknown')}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Suggested Fix:*\n{explanation.get('suggestion', 'Check logs')}"
            }
        }
    ]
    
    if so_solutions:
        solution_text = "*Top StackOverflow Solutions:*\n"
        for sol in so_solutions:
            solution_text += f"• <{sol['link']}|{sol['title']}> ({sol['score']} upvotes)\n"
            
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": solution_text
            }
        })
        
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "View Build Logs"
                },
                "style": "primary",
                "url": build_url
            }
        ]
    })
    
    try:
        response = slack_client.chat_postMessage(
            channel=SLACK_CHANNEL,
            blocks=blocks,
            text=f"CI Failure in {repository_name}"
        )
        return True
    except SlackApiError as e:
        logger.error(f"Error posting to Slack: {e.response['error']}")
        return False

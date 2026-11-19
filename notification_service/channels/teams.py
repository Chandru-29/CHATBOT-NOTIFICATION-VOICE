import httpx
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger("notification_service.teams")

async def send_teams_notification(
    webhook_url: str,
    title: str,
    clean_markdown_text: str,
    user_query: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    app_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sends an Adaptive Card to MS Teams via Incoming Webhook / Workflows connector.

    Returns:
        Dict: {"success": bool, "status_code": Optional[int], "error": Optional[str]}
    """
    if not webhook_url or not webhook_url.strip():
        return {"success": False, "error": "Teams webhook URL is missing"}

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build facts list
    facts = []
    if user_query:
        clean_q = user_query.strip()
        facts.append({"title": "Query:", "value": (clean_q[:250] + "...") if len(clean_q) > 250 else clean_q})
    if user_id and user_id != "unknown_user":
        facts.append({"title": "User:", "value": str(user_id)})
    if app_name and app_name not in ("unknown_app", "chat_boat_sql"):
        facts.append({"title": "App:", "value": str(app_name)})
    if session_id and session_id != "default_session":
        facts.append({"title": "Session:", "value": str(session_id)})
    facts.append({"title": "Time:", "value": now_str})

    header_text = "📦 Mobillor AI Assistant Alert" if not title or title in ("Operational Notification", "Operational Alert") else f"📦 Mobillor AI Alert: {title}"

    adaptive_card = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "version": "1.5",
                    "type": "AdaptiveCard",
                    "msteams": {
                        "width": "Full"
                    },
                    "body": [
                        {
                            "type": "Container",
                            "style": "emphasis",
                            "bleed": True,
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": header_text,
                                    "weight": "Bolder",
                                    "size": "Medium",
                                    "color": "Accent",
                                    "wrap": True
                                }
                            ]
                        },
                        {
                            "type": "FactSet",
                            "facts": facts,
                            "spacing": "Medium"
                        },
                        {
                            "type": "TextBlock",
                            "text": clean_markdown_text,
                            "wrap": True,
                            "spacing": "Medium"
                        }
                    ]
                }
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook_url.strip(),
                json=adaptive_card,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code in (200, 202):
                logger.info(" [MS Teams] Notification delivered successfully.")
                return {"success": True, "status_code": response.status_code}
            else:
                err_msg = f"Teams webhook responded with status {response.status_code}: {response.text}"
                logger.warning(f" [MS Teams] {err_msg}")
                return {"success": False, "status_code": response.status_code, "error": err_msg}

    except Exception as e:
        err_msg = f"Teams notification failed: {str(e)}"
        logger.error(f"❌ [MS Teams] {err_msg}")
        return {"success": False, "error": err_msg}


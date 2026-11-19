import asyncio
import concurrent.futures
import logging
from typing import Dict, Any, Optional

from notification_service.dispatcher import dispatch_notifications

logger = logging.getLogger("notification_service.tool")

def _run_async_safe(coroutine):
    """
    Safely runs an async coroutine whether called from a sync thread or inside an active event loop.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, coroutine)
            return future.result()
    else:
        return asyncio.run(coroutine)


def send_notification(
    content: str,
    channels: str = "teams",
    user_query: Optional[str] = None,
    title: Optional[str] = None,
    recipient: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sends notification messages, reports, or data tables to external enterprise channels (MS Teams, Gmail, Outlook, WhatsApp).

    Args:
        content: The formatted Markdown table, summary, or text message to send.
        channels: Target channels separated by comma, e.g. 'teams', 'gmail', 'outlook', 'whatsapp'. Default is 'teams'.
        user_query: The user's original request or prompt that initiated this alert (e.g. 'Show top 4 GRN and email to me in gmail').
        title: Optional title or subject for the notification.
        recipient: Optional specific recipient email address or phone number (for WhatsApp).

    Returns:
        dict: Delivery status and results per channel.
    """
    if not content or not content.strip():
        return {"success": False, "error": "Notification content cannot be empty."}

    channel_list = [c.strip().lower() for c in channels.split(",") if c.strip()]
    if not channel_list:
        channel_list = ["teams"]

    logger.info(f"[Tool] send_notification called for channels: {channel_list}, recipient: {recipient}")

    query_str = user_query or title or "Operational Alert"
    targets = {}
    if recipient and recipient.strip():
        clean_rec = recipient.strip()
        targets = {
            "gmail_to": clean_rec,
            "outlook_to": clean_rec,
            "whatsapp_to": clean_rec,
            "recipient": clean_rec
        }

    try:
        result = _run_async_safe(
            dispatch_notifications(
                adk_raw_response=content,
                user_query=query_str,
                requested_channels=channel_list,
                channel_targets=targets if targets else None,
                force_notify=True
            )
        )
        rec_msg = f" (Recipient: {recipient})" if recipient else ""
        return {
            "success": True,
            "message": f"Notification successfully sent to {', '.join(channel_list)}{rec_msg}.",
            "details": result
        }
    except Exception as e:
        logger.error(f"[Tool] Failed to send notification: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to send notification: {str(e)}"
        }


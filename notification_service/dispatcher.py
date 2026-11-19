import os
import re
import asyncio
import logging
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from notification_service.extractor import extract_clean_adk_response
from notification_service.channels.teams import send_teams_notification
from notification_service.channels.gmail import send_gmail_notification
from notification_service.channels.outlook import send_outlook_notification
from notification_service.channels.whatsapp import send_whatsapp_notification

load_dotenv()
logger = logging.getLogger("notification_service.dispatcher")

# Common conversational greetings that should NOT trigger notifications
TRIVIAL_GREETINGS = {
    "hi", "hello", "hey", "good morning", "good evening", 
    "thanks", "thank you", "ok", "okay", "bye", "test"
}

def should_skip_notification(user_query: Optional[str], clean_text: str) -> bool:
    """
    Checks if message is too trivial to send as a corporate alert (spam prevention).
    """
    if not clean_text or not clean_text.strip():
        return True

    if user_query:
        query_norm = user_query.strip().lower()
        if query_norm in TRIVIAL_GREETINGS and len(clean_text) < 150:
            return True

    return False


def extract_emails_from_query(query: Optional[str]) -> List[str]:
    """
    Extracts email addresses mentioned naturally in the query or payload.
    """
    if not query:
        return []
    return re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', query)


def extract_phone_from_query(query: Optional[str]) -> Optional[str]:
    """
    Extracts phone numbers mentioned in the user query for WhatsApp routing.
    """
    if not query:
        return None
    match = re.search(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4,6}\b', query)
    return match.group(0) if match else None


def detect_channels_from_query(user_query: Optional[str]) -> List[str]:
    """
    Detects notification channels naturally requested in the user's chat query:
    1. 'teams' with action verb -> MS Teams
    2. 'whatsapp' with action verb -> WhatsApp
    3. Explicit 'gmail' word or @gmail address -> Gmail
    4. General 'send a mail' / 'email me' / 'outlook' / corporate email -> Outlook or Gmail
    """
    if not user_query:
        return []

    q = user_query.lower()
    detected = set()

    # 1. MS Teams Pattern
    if re.search(r"\b(send|push|post|share|notify|alert)\b.*\b(teams|ms\s*teams)\b", q):
        detected.add("teams")

    # 2. WhatsApp Pattern
    if re.search(r"\b(send|push|share|notify|alert)\b.*\b(whatsapp|wa)\b", q) or re.search(r"\bwhatsapp\s+(me|this|the)\b", q):
        detected.add("whatsapp")

    # 3. Explicit GMAIL Check:
    if ("gmail" in q and re.search(r"\b(send|email|mail|push|share|to|on|in)\b.*\bgmail\b", q)) or "@gmail.com" in q:
        detected.add("gmail")

    # 4. OUTLOOK & General Email / Specific Email address:
    elif re.search(r"\boutlook\b", q) or \
         re.search(r"\b(email|mail)\s+(this|me|to|the|a|in)\b", q) or \
         re.search(r"\b(send|push|share)\b.*?\b(email|mail|a\s+mail)\b", q) or \
         bool(extract_emails_from_query(user_query)):
        
        has_outlook = bool(os.getenv("AZURE_CLIENT_ID") or os.getenv("OUTLOOK_SMTP_PASSWORD"))
        if has_outlook or not os.getenv("GMAIL_SMTP_USER"):
            detected.add("outlook")
        else:
            detected.add("gmail")

    return list(detected)


async def dispatch_notifications(
    adk_raw_response: Any,
    user_query: Optional[str] = None,
    user_id: Optional[str] = "unknown_user",
    session_id: Optional[str] = "default_session",
    app_name: Optional[str] = "chat_boat_sql",
    requested_channels: Optional[List[str]] = None,
    channel_targets: Optional[Dict[str, str]] = None,
    force_notify: bool = False
) -> Dict[str, Any]:
    """
    Central Asynchronous Dispatcher:
    1. Extracts clean text & markdown tables from raw ADK events.
    2. Filters out spam / trivial greetings (unless force_notify is True).
    3. Resolves active channels via 3-tier hierarchy:
       - Priority 1: Explicit payload list (UI toggle / parameter)
       - Priority 2: Natural language intent detected in user_query (e.g. "send to teams", "send a mail")
       - Priority 3: DEFAULT_NOTIFICATION_CHANNELS from .env
    4. Executes non-blocking parallel fan-out delivery across all active channels.

    Returns:
        Dict of results per channel: {"teams": {...}, "gmail": {...}, ...}
    """
    results: Dict[str, Any] = {}

    try:
        # Step 1: Extract Clean Text & Metadata from ADK Response
        clean_text, metadata = extract_clean_adk_response(adk_raw_response)
        
        if not clean_text:
            logger.info(" [Dispatcher] Extracted text is empty. Skipping notification dispatch.")
            return {"status": "skipped", "reason": "empty_text"}

        # Step 2: Spam / Greeting Filter
        if not force_notify and should_skip_notification(user_query, clean_text):
            logger.info(f" [Dispatcher] Query '{user_query}' identified as greeting/trivial. Bypassing notification.")
            return {"status": "bypassed", "reason": "greeting_filter"}

        # Step 3: Determine Active Channels (3-Tier Priority)
        # Priority 1: Explicit payload list from UI
        raw_channels = requested_channels

        # Priority 2: Natural language chat intent in user_query
        if not raw_channels and user_query:
            detected = detect_channels_from_query(user_query)
            if detected:
                logger.info(f"🎯 [Dispatcher] Natural language detected channels: {detected} from query: '{user_query}'")
                raw_channels = detected

        # Priority 3: Global defaults from .env
        if not raw_channels:
            env_defaults = os.getenv("DEFAULT_NOTIFICATION_CHANNELS", "")
            raw_channels = [c.strip() for c in env_defaults.split(",") if c.strip()]

        active_channels = [c.lower() for c in raw_channels if c.lower() in ("teams", "gmail", "outlook", "whatsapp")]

        if not active_channels:
            logger.info(" [Dispatcher] No active notification channels configured or requested.")
            return {"status": "skipped", "reason": "no_channels_active"}

        targets = channel_targets or {}

        # 1. Dynamic email & phone auto-extraction from user query or target params
        dynamic_emails = extract_emails_from_query(user_query)
        dynamic_email = targets.get("recipient") or (dynamic_emails[0] if dynamic_emails else None)
        dynamic_phone = targets.get("recipient") or extract_phone_from_query(user_query)

        subject_title = (user_query[:55] + "...") if user_query and len(user_query) > 55 else (user_query or "Operational Alert")

        task_mapping: Dict[str, Any] = {}

        # -------------------------------------------------------------
        # Channel 1: Microsoft Teams
        # -------------------------------------------------------------
        if "teams" in active_channels:
            teams_webhook = targets.get("teams_webhook") or os.getenv("TEAMS_WEBHOOK_URL")
            if teams_webhook:
                task_mapping["teams"] = send_teams_notification(
                    webhook_url=teams_webhook,
                    title=subject_title,
                    clean_markdown_text=clean_text,
                    user_query=user_query,
                    session_id=session_id,
                    user_id=user_id,
                    app_name=app_name
                )
            else:
                logger.warning("⚠️ [Dispatcher] 'teams' requested but TEAMS_WEBHOOK_URL is not set.")
                results["teams"] = {"success": False, "error": "TEAMS_WEBHOOK_URL not configured"}

        # -------------------------------------------------------------
        # Channel 2: Gmail
        # -------------------------------------------------------------
        if "gmail" in active_channels:
            gmail_to = targets.get("gmail_to") or dynamic_email or os.getenv("GMAIL_DEFAULT_RECIPIENT")
            smtp_user = os.getenv("GMAIL_SMTP_USER")
            smtp_pwd = os.getenv("GMAIL_SMTP_APP_PASSWORD")
            smtp_host = os.getenv("GMAIL_SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.getenv("GMAIL_SMTP_PORT", "587"))

            if gmail_to and smtp_user and smtp_pwd:
                logger.info(f"📬 [Dispatcher] Dispatching Gmail notification to: {gmail_to}")
                task_mapping["gmail"] = send_gmail_notification(
                    to_email=gmail_to,
                    subject=subject_title,
                    clean_markdown_text=clean_text,
                    smtp_user=smtp_user,
                    smtp_password=smtp_pwd,
                    user_query=user_query,
                    user_id=user_id,
                    session_id=session_id,
                    app_name=app_name,
                    smtp_host=smtp_host,
                    smtp_port=smtp_port
                )
            else:
                logger.warning("⚠️ [Dispatcher] 'gmail' requested but Gmail credentials or recipient missing.")
                results["gmail"] = {"success": False, "error": "Gmail credentials or recipient missing"}

        # -------------------------------------------------------------
        # Channel 3: Outlook / Office 365
        # -------------------------------------------------------------
        if "outlook" in active_channels:
            outlook_to = targets.get("outlook_to") or dynamic_email or os.getenv("OUTLOOK_DEFAULT_RECIPIENT")
            tenant_id = os.getenv("AZURE_TENANT_ID")
            client_id = os.getenv("AZURE_CLIENT_ID")
            client_secret = os.getenv("AZURE_CLIENT_SECRET")
            sender_email = os.getenv("OUTLOOK_SENDER_EMAIL")
            smtp_user = os.getenv("OUTLOOK_SMTP_USER")
            smtp_pwd = os.getenv("OUTLOOK_SMTP_PASSWORD")

            if outlook_to and ((tenant_id and client_id and client_secret and sender_email) or ((smtp_user or sender_email) and smtp_pwd)):
                logger.info(f"📬 [Dispatcher] Dispatching Outlook notification to: {outlook_to}")
                task_mapping["outlook"] = send_outlook_notification(
                    recipient_email=outlook_to,
                    subject=subject_title,
                    clean_markdown_text=clean_text,
                    user_query=user_query,
                    tenant_id=tenant_id,
                    client_id=client_id,
                    client_secret=client_secret,
                    sender_email=sender_email,
                    smtp_user=smtp_user,
                    smtp_password=smtp_pwd
                )
            else:
                logger.warning("⚠️ [Dispatcher] 'outlook' requested but Outlook credentials or recipient missing.")
                results["outlook"] = {"success": False, "error": "Outlook credentials or recipient missing"}

        # -------------------------------------------------------------
        # Channel 4: WhatsApp (Meta Cloud API)
        # -------------------------------------------------------------
        if "whatsapp" in active_channels:
            wa_to = targets.get("whatsapp_to") or dynamic_phone or os.getenv("WHATSAPP_DEFAULT_RECIPIENT")
            wa_phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
            wa_token = os.getenv("WHATSAPP_ACCESS_TOKEN")

            if wa_to and wa_phone_id and wa_token:
                logger.info(f"📬 [Dispatcher] Dispatching WhatsApp notification to: {wa_to}")
                task_mapping["whatsapp"] = send_whatsapp_notification(
                    phone_number_id=wa_phone_id,
                    access_token=wa_token,
                    recipient_phone=wa_to,
                    clean_markdown_text=clean_text,
                    title=subject_title
                )
            else:
                logger.warning("⚠️ [Dispatcher] 'whatsapp' requested but WhatsApp credentials or recipient missing.")
                results["whatsapp"] = {"success": False, "error": "WhatsApp credentials or recipient missing"}

        # Step 4: Parallel Fan-out Delivery (Asyncio Gather)
        if task_mapping:
            channel_names = list(task_mapping.keys())
            coroutines = list(task_mapping.values())

            # return_exceptions=True isolates failures so 1 down channel does not affect others
            executed_results = await asyncio.gather(*coroutines, return_exceptions=True)

            for channel, res in zip(channel_names, executed_results):
                if isinstance(res, Exception):
                    logger.error(f" [Dispatcher] {channel} encountered exception: {str(res)}")
                    results[channel] = {"success": False, "error": str(res)}
                else:
                    results[channel] = res

        return results

    except Exception as e:
        logger.error(f" [Dispatcher Unhandled Exception]: {str(e)}")
        return {"status": "error", "error": str(e)}

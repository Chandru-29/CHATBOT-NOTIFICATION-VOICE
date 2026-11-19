import re
import logging
import httpx
from typing import Dict, Any, Optional

logger = logging.getLogger("notification_service.whatsapp")

def convert_markdown_table_to_whatsapp_text(markdown_text: str) -> str:
    """
    Parses Markdown tables and transforms them into clean, 
    compact bullet points formatted with WhatsApp-supported typography (*bold*, _italic_).
    """
    if not markdown_text:
        return ""

    lines = markdown_text.strip().split("\n")
    processed_lines = []
    in_table = False
    headers = []

    for line in lines:
        line_clean = line.strip()

        # Check if line is a markdown table row
        if line_clean.startswith("|") and line_clean.endswith("|"):
            cells = [c.strip() for c in line_clean.split("|")[1:-1]]

            # Detect separator row (e.g., |---|---| or |:---|:---|)
            if all(re.match(r"^:?-+:?$", c) for c in cells):
                in_table = True
                continue

            if not in_table:
                # First row represents table headers
                headers = cells
                in_table = True
                continue
            else:
                # Content rows -> transform into key-value bullet cards
                row_items = [f"*{h}*: {val}" for h, val in zip(headers, cells) if val]
                row_str = "• " + " | ".join(row_items)
                processed_lines.append(row_str)
        else:
            in_table = False
            # Transform standard markdown syntax into WhatsApp formatting
            # 1. Headers (### Header -> *Header*)
            transformed = re.sub(r"^#{1,6}\s*(.*)", r"*\1*", line_clean)
            # 2. Convert standard markdown **bold** to WhatsApp *bold*
            transformed = re.sub(r"\*\*(.*?)\*\*", r"*\1*", transformed)
            processed_lines.append(transformed)

    return "\n".join(processed_lines)


async def send_whatsapp_notification(
    phone_number_id: str,
    access_token: str,
    recipient_phone: str,
    clean_markdown_text: str,
    title: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transforms markdown response and dispatches a WhatsApp message via Meta Cloud API.
    
    Returns:
        Dict: {"success": bool, "status_code": Optional[int], "error": Optional[str]}
    """
    if not phone_number_id or not access_token or not recipient_phone:
        return {"success": False, "error": "Missing WhatsApp Phone ID, Access Token, or Recipient Number"}

    # 1. Format text for WhatsApp mobile display
    formatted_body = convert_markdown_table_to_whatsapp_text(clean_markdown_text)

    # 2. Add header
    header_text = f"📦 *Mobillor AI Warehouse Alert*" if not title else f"📦 *Mobillor AI Alert: {title}*"
    full_message = f"{header_text}\n\n{formatted_body}"

    # 3. Guard against Meta WhatsApp 4096 character limit
    if len(full_message) > 4000:
        full_message = full_message[:3900] + "\n\n_...[Report truncated for WhatsApp. View full details in Web App]_"

    # Sanitize phone number (remove +, spaces, hyphens)
    clean_phone = re.sub(r"[^0-9]", "", recipient_phone.strip())

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": clean_phone,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": full_message
        }
    }

    url = f"https://graph.facebook.com/v19.0/{phone_number_id.strip()}/messages"
    headers = {
        "Authorization": f"Bearer {access_token.strip()}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            res = await client.post(url, headers=headers, json=payload)
            if res.status_code in (200, 201):
                logger.info(f"✅ [WhatsApp] Message delivered to {clean_phone}")
                return {"success": True, "status_code": res.status_code}
            else:
                err_msg = f"Meta WhatsApp API returned {res.status_code}: {res.text}"
                logger.warning(f"⚠️ [WhatsApp] {err_msg}")
                return {"success": False, "status_code": res.status_code, "error": err_msg}

    except Exception as e:
        err_msg = f"WhatsApp send error: {str(e)}"
        logger.error(f"❌ [WhatsApp] {err_msg}")
        return {"success": False, "error": err_msg}


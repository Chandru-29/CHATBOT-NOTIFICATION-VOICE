import logging
import httpx
from typing import Dict, Any, Optional
import markdown
import aiosmtplib
from email.message import EmailMessage

logger = logging.getLogger("notification_service.outlook")

async def _send_via_graph_api(
    tenant_id: str,
    client_id: str,
    client_secret: str,
    sender_upn: str,
    recipient_email: str,
    subject: str,
    html_body: str
) -> Dict[str, Any]:
    """
    Acquires OAuth2 token from Microsoft Entra ID (Azure AD) and dispatches email via Graph API.
    """
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    token_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }

    async with httpx.AsyncClient(timeout=12.0) as client:
        # Step 1: Get Access Token
        token_res = await client.post(token_url, data=token_data)
        if token_res.status_code != 200:
            return {"success": False, "error": f"Azure AD token acquisition failed: {token_res.text}"}

        access_token = token_res.json().get("access_token")
        if not access_token:
            return {"success": False, "error": "No access token received from Azure AD"}

        # Step 2: Call Microsoft Graph sendMail
        send_url = f"https://graph.microsoft.com/v1.0/users/{sender_upn}/sendMail"
        email_payload = {
            "message": {
                "subject": f"Mobillor AI: {subject}",
                "body": {
                    "contentType": "HTML",
                    "content": html_body
                },
                "toRecipients": [
                    {"emailAddress": {"address": recipient_email}}
                ]
            },
            "saveToSentItems": "false"
        }

        send_res = await client.post(
            send_url,
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json=email_payload
        )

        if send_res.status_code in (200, 202):
            logger.info(f"✅ [Outlook Graph] Notification delivered to {recipient_email}")
            return {"success": True, "status_code": send_res.status_code}
        else:
            return {"success": False, "status_code": send_res.status_code, "error": send_res.text}


async def send_outlook_notification(
    recipient_email: str,
    subject: str,
    clean_markdown_text: str,
    user_query: Optional[str] = None,
    tenant_id: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    sender_email: Optional[str] = None,
    smtp_user: Optional[str] = None,
    smtp_password: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sends an Outlook notification using Microsoft Graph API (OAuth2) or Office 365 SMTP fallback.
    """
    if not recipient_email:
        return {"success": False, "error": "Recipient email is missing"}

    query_html_block = ""
    if user_query and user_query.strip():
        query_html_block = f"""
        <div style="background: #f8fafc; border-left: 4px solid #0078d4; padding: 12px 16px; margin-bottom: 18px; border-radius: 0 4px 4px 0; border: 1px solid #e2e8f0; border-left-width: 4px;">
          <span style="font-size: 11px; font-weight: 700; color: #64748b; letter-spacing: 0.5px; text-transform: uppercase; display: block; margin-bottom: 4px;">USER QUERY</span>
          <p style="margin: 0; font-size: 14px; color: #0f172a; font-weight: 500; font-style: italic;">"{user_query.strip()}"</p>
        </div>
        """

    # Render HTML from markdown
    rendered_html = markdown.markdown(clean_markdown_text, extensions=["tables", "fenced_code"])
    styled_html = f"""<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #334155; line-height: 1.6; max-width: 650px; padding: 18px; border: 1px solid #e2e8f0; border-radius: 8px;">
        <h3 style="color: #0f172a; margin-top: 0;">Mobillor AI Assistant Alert</h3>
        {query_html_block}
        {rendered_html}
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin-top: 24px;" />
        <span style="font-size: 11px; color: #64748b;">Automated notification from Mobillor AI Platform</span>
    </div>"""

    # Mode 1: Microsoft Graph API (Enterprise Azure AD)
    if tenant_id and client_id and client_secret and sender_email:
        try:
            return await _send_via_graph_api(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret,
                sender_upn=sender_email,
                recipient_email=recipient_email,
                subject=subject,
                html_body=styled_html
            )
        except Exception as e:
            logger.error(f" [Outlook Graph] Failed: {str(e)}")
            return {"success": False, "error": str(e)}

    # Mode 2: Office 365 SMTP Fallback
    elif (smtp_user or sender_email) and smtp_password:
        active_user = smtp_user or sender_email
        try:
            msg = EmailMessage()
            msg["Subject"] = f"[Mobillor AI] {subject}"
            msg["From"] = active_user
            msg["To"] = recipient_email
            msg.set_content(clean_markdown_text)
            msg.add_alternative(styled_html, subtype="html")

            await aiosmtplib.send(
                msg,
                hostname="smtp.office365.com",
                port=587,
                start_tls=True,
                username=active_user.strip(),
                password=smtp_password.strip(),
                timeout=15.0
            )
            logger.info(f" [Outlook SMTP] Delivered to {recipient_email}")
            return {"success": True}
        except Exception as e:
            logger.error(f" [Outlook SMTP] Failed: {str(e)}")
            return {"success": False, "error": str(e)}

    return {"success": False, "error": "Insufficient Outlook credentials (need Azure AD credentials or O365 SMTP)"}


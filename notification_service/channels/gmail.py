import logging
import asyncio
import smtplib
from datetime import datetime
from email.message import EmailMessage
from typing import Dict, Any, Optional
import markdown

logger = logging.getLogger("notification_service.gmail")

def _send_sync_smtp(
    to_email: str,
    subject: str,
    clean_markdown_text: str,
    styled_html: str,
    smtp_user: str,
    smtp_password: str,
    smtp_host: str = "smtp.gmail.com",
    smtp_port: int = 587
) -> Dict[str, Any]:
    """
    Synchronous fallback using Python standard smtplib (which works reliably across all Windows/Python versions).
    Executed inside asyncio.to_thread to maintain non-blocking asynchronous behavior.
    """
    msg = EmailMessage()
    msg["Subject"] = f"[Mobillor AI] {subject}"
    msg["From"] = f"Mobillor AI Assistant <{smtp_user}>"
    msg["To"] = to_email

    msg.set_content(clean_markdown_text)
    msg.add_alternative(styled_html, subtype="html")

    server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
    try:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        return {"success": True}
    finally:
        try:
            server.quit()
        except Exception:
            pass


async def send_gmail_notification(
    to_email: str,
    subject: str,
    clean_markdown_text: str,
    smtp_user: str,
    smtp_password: str,
    user_query: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    app_name: Optional[str] = None,
    smtp_host: str = "smtp.gmail.com",
    smtp_port: int = 587
) -> Dict[str, Any]:
    """
    Sends a responsive, branded HTML email notification via Gmail SMTP.
    Includes user query box, timestamp, metadata chips, and formatted tables.
    Uses non-blocking threaded execution with standard smtplib for maximum reliability.
    """
    if not to_email or not smtp_user or not smtp_password:
        return {"success": False, "error": "Missing recipient email or SMTP credentials"}

    # Auto-fix common email typo if present (e.g. @gmai.com -> @gmail.com)
    clean_user = smtp_user.strip()
    if clean_user.endswith("@gmai.com"):
        clean_user = clean_user.replace("@gmai.com", "@gmail.com")

    clean_pwd = smtp_password.strip().replace(" ", "")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Render markdown to styled HTML
        html_body = markdown.markdown(
            clean_markdown_text,
            extensions=["tables", "fenced_code"]
        )

        query_html_block = ""
        if user_query and user_query.strip():
            query_html_block = f"""
            <div style="background: #f8fafc; border-left: 4px solid #2563eb; padding: 14px 18px; margin-bottom: 22px; border-radius: 0 6px 6px 0; border: 1px solid #e2e8f0; border-left-width: 4px;">
              <span style="font-size: 11px; font-weight: 700; color: #64748b; letter-spacing: 0.6px; text-transform: uppercase; display: block; margin-bottom: 5px;">USER QUERY</span>
              <p style="margin: 0; font-size: 14.5px; color: #0f172a; font-weight: 500; font-style: italic;">"{user_query.strip()}"</p>
            </div>
            """

        meta_info = f"""
        <div style="margin-bottom: 18px; font-size: 12px; color: #64748b; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">
          <span><strong>Generated:</strong> {now_str}</span>
          {f" &nbsp;|&nbsp; <span><strong>User:</strong> {user_id}</span>" if user_id and user_id != 'unknown_user' else ""}
          {f" &nbsp;|&nbsp; <span><strong>Session:</strong> {session_id}</span>" if session_id and session_id != 'default_session' else ""}
        </div>
        """

        styled_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: #f1f5f9;
      margin: 0;
      padding: 24px;
      color: #334155;
    }}
    .email-card {{
      max-width: 680px;
      background: #ffffff;
      border-radius: 8px;
      border: 1px solid #e2e8f0;
      margin: 0 auto;
      overflow: hidden;
      box-shadow: 0 2px 4px rgba(0,0,0,0.06);
    }}
    .header {{
      background: #0f172a;
      color: #ffffff;
      padding: 20px 28px;
    }}
    .header h2 {{
      margin: 0;
      font-size: 19px;
      font-weight: 600;
      letter-spacing: 0.2px;
    }}
    .content {{
      padding: 28px;
      line-height: 1.6;
      font-size: 14.5px;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      margin: 18px 0;
      font-size: 14px;
    }}
    th, td {{
      border: 1px solid #cbd5e1;
      padding: 10px 14px;
      text-align: left;
    }}
    th {{
      background-color: #f8fafc;
      font-weight: 600;
      color: #0f172a;
    }}
    tr:nth-child(even) {{
      background-color: #f8fafc;
    }}
    .footer {{
      background: #f8fafc;
      padding: 14px 28px;
      font-size: 12px;
      color: #64748b;
      text-align: center;
      border-top: 1px solid #e2e8f0;
    }}
  </style>
</head>
<body>
  <div class="email-card">
    <div class="header">
      <h2>Mobillor AI Assistant Alert</h2>
    </div>
    <div class="content">
      {query_html_block}
      {meta_info}
      {html_body}
    </div>
    <div class="footer">
      Automated warehouse & operational alert generated by Mobillor Multi-Agent AI Platform.
    </div>
  </div>
</body>
</html>"""

        plain_text = f"USER QUERY:\n{user_query.strip()}\n\n{clean_markdown_text}" if user_query and user_query.strip() else clean_markdown_text

        # Run non-blocking in thread pool
        res = await asyncio.to_thread(
            _send_sync_smtp,
            to_email=to_email.strip(),
            subject=subject,
            clean_markdown_text=plain_text,
            styled_html=styled_html,
            smtp_user=clean_user,
            smtp_password=clean_pwd,
            smtp_host=smtp_host,
            smtp_port=smtp_port
        )

        logger.info(f"✅ [Gmail] Notification delivered to {to_email}")
        return res

    except Exception as e:
        err_msg = f"Gmail SMTP send failed: {str(e)}"
        logger.error(f"❌ [Gmail] {err_msg}")
        return {"success": False, "error": err_msg}

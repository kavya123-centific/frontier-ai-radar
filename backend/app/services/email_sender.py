"""
email_sender.py
---------------
Multi-provider email delivery with automatic fallback.

Provider priority (set ONE block in .env / Render environment variables):

  1. SendGrid API (RECOMMENDED — sends to ANY email, no domain verification)
     Free tier: 100 emails/day. Sign up at sendgrid.com
       SENDGRID_API_KEY=SG.xxxxxxxxxxxx
       SENDGRID_FROM=bandla.kavya@centific.com

  2. Resend API (limited to own email on free plan without domain verification)
       RESEND_API_KEY=re_xxxxxxxxxxxx
       RESEND_FROM=AI Radar <onboarding@resend.dev>

  3. Office 365 / Outlook SMTP (if on Microsoft corporate network)
       SMTP_EMAIL=you@company.com
       SMTP_PASSWORD=your-password
       SMTP_HOST=smtp.office365.com
       SMTP_PORT=587

  4. Gmail SMTP (home network only — blocked on most corporate Wi-Fi)
       SMTP_EMAIL=you@gmail.com
       SMTP_PASSWORD=16-char-app-password
       SMTP_HOST=smtp.gmail.com
       SMTP_PORT=465

  If nothing is configured → email is skipped gracefully (no error).
"""

import base64
import json
import logging
import os
import smtplib
import urllib.error
import urllib.request
from email.message import EmailMessage
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Placeholder values that should never be treated as real credentials
_PLACEHOLDERS = {
    "", "abcd", "abcdefghijklmnop", "password", "your-password",
    "xxxx-xxxx-xxxx-xxxx", "re_xxxxxxxxxxxx", "your-resend-key",
    "sg.xxxxxxxxxxxx",
}


# ── Email body builder ─────────────────────────────────────────────────────

def _build_text_body(findings: List[Dict[str, Any]]) -> str:
    lines = [
        "🛰 FRONTIER AI RADAR — Daily Intelligence Digest",
        "=" * 58, "",
        "TODAY'S TOP SIGNALS:", "",
    ]
    for i, f in enumerate(findings[:5], 1):
        score    = f.get("final_score", 0) or 0
        title    = f.get("title", "Untitled")
        summary  = (f.get("summary", "") or "")[:130]
        why      = (f.get("why_matters", "") or "")[:100]
        url      = f.get("source_url", "")
        category = (f.get("category", "") or "").replace("_", " ").upper()
        conf     = f.get("confidence_score", 0.8) or 0.8
        cluster  = f.get("topic_cluster", "general") or "general"
        lines.extend([
            f"{i}. [{score:.1f}] {title}",
            f"   Category: {category}  |  Cluster: {cluster}  |  Confidence: {conf:.0%}",
            f"   {summary}...",
            f"   💡 {why}",
            f"   → {url}", "",
        ])
    lines.extend([
        "=" * 58, "",
        "Full PDF digest is attached to this email.",
        "Dashboard: http://localhost:8501", "",
        "—",
        "Frontier AI Radar · Automated Intelligence System",
    ])
    return "\n".join(lines)


def _build_html_body(findings: List[Dict[str, Any]]) -> str:
    """Rich HTML email body."""
    rows = ""
    for i, f in enumerate(findings[:5], 1):
        score    = f.get("final_score", 0) or 0
        title    = f.get("title", "Untitled")
        summary  = (f.get("summary", "") or "")[:200]
        why      = (f.get("why_matters", "") or "")[:150]
        url      = f.get("source_url", "") or "#"
        conf     = f.get("confidence_score", 0.8) or 0.8
        cluster  = f.get("topic_cluster", "general") or "general"
        evidence = f.get("evidence", "") or ""
        color    = "#059669" if score >= 7 else "#d97706" if score >= 4 else "#6b7280"
        rows += f"""
        <tr>
          <td style="padding:16px;border-bottom:1px solid #e2e8f0;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
              <span style="background:{color};color:white;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:bold;">{score:.1f}</span>
              <span style="background:#e0f2fe;color:#0369a1;padding:2px 8px;border-radius:12px;font-size:11px;">{cluster}</span>
              <span style="background:#f0fdf4;color:#166534;padding:2px 8px;border-radius:12px;font-size:11px;">{conf:.0%} confidence</span>
            </div>
            <div style="font-weight:600;font-size:15px;color:#0f172a;margin-bottom:4px;">{i}. {title}</div>
            <div style="color:#475569;font-size:13px;margin-bottom:6px;">{summary}</div>
            <div style="background:#f0fdf4;border-left:3px solid #22c55e;padding:6px 10px;font-size:12px;color:#166534;margin-bottom:6px;">💡 {why}</div>
            {"<div style='background:#fefce8;border-left:3px solid #eab308;padding:6px 10px;font-size:12px;color:#713f12;margin-bottom:6px;'>📎 " + evidence + "</div>" if evidence else ""}
            <a href="{url}" style="color:#2563eb;font-size:12px;">🔗 View source →</a>
          </td>
        </tr>"""

    return f"""
    <html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f8fafc;margin:0;padding:20px;">
      <div style="max-width:640px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 4px 6px rgba(0,0,0,0.07);">
        <div style="background:linear-gradient(135deg,#0d1b2a,#1b4f8a);padding:24px;text-align:center;">
          <div style="font-size:28px;">🛰</div>
          <div style="color:white;font-size:20px;font-weight:700;margin-top:8px;">Frontier AI Radar</div>
          <div style="color:#94a3b8;font-size:13px;margin-top:4px;">Daily Intelligence Digest · {len(findings)} signals today</div>
        </div>
        <table width="100%" cellpadding="0" cellspacing="0">{rows}</table>
        <div style="padding:16px;text-align:center;background:#f8fafc;color:#94a3b8;font-size:12px;">
          Full PDF digest attached · Dashboard: <a href="http://localhost:8501">localhost:8501</a>
        </div>
      </div>
    </body></html>"""


# ── Provider 1: SendGrid API ───────────────────────────────────────────────

def _send_via_sendgrid(
    api_key: str,
    from_addr: str,
    recipients: List[str],
    subject: str,
    html_body: str,
    text_body: str,
    pdf_path: str,
) -> bool:
    """
    Send via SendGrid HTTP API (port 443).
    Free tier: 100 emails/day to ANY email address — no domain verification needed.
    """
    attachments = []
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as fh:
            attachments = [{
                "content":     base64.b64encode(fh.read()).decode(),
                "filename":    "frontier_ai_radar_digest.pdf",
                "type":        "application/pdf",
                "disposition": "attachment",
            }]

    payload = {
        "personalizations": [{"to": [{"email": r} for r in recipients]}],
        "from":    {"email": from_addr},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": text_body},
            {"type": "text/html",  "value": html_body},
        ],
    }
    if attachments:
        payload["attachments"] = attachments

    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        },
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=15)
        logger.info(f"SendGrid: email sent successfully to {recipients}")
        return True
    except urllib.error.HTTPError as e:
        logger.error(f"SendGrid error {e.code}: {e.read().decode()}")
        return False
    except Exception as e:
        logger.error(f"SendGrid failed: {type(e).__name__}: {e}")
        return False


# ── Provider 2: Resend API ─────────────────────────────────────────────────

def _send_via_resend(
    api_key: str,
    from_addr: str,
    recipients: List[str],
    subject: str,
    html_body: str,
    text_body: str,
    pdf_path: str,
) -> bool:
    """
    Send via Resend HTTP API (port 443).
    NOTE: Free plan only sends to the account owner's email unless domain is verified.
    """
    payload: Dict = {
        "from":    from_addr,
        "to":      recipients,
        "subject": subject,
        "html":    html_body,
        "text":    text_body,
    }
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as fh:
            payload["attachments"] = [{
                "filename": "frontier_ai_radar_digest.pdf",
                "content":  base64.b64encode(fh.read()).decode(),
            }]

    try:
        import httpx
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=15.0,
        )
        if resp.status_code in (200, 201):
            logger.info(f"Resend: email sent successfully, id={resp.json().get('id')}")
            return True
        else:
            logger.error(f"Resend error {resp.status_code}: {resp.text}")
            return False
    except ImportError:
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read())
                logger.info(f"Resend: email sent, id={result.get('id')}")
                return True
        except urllib.error.HTTPError as e:
            logger.error(f"Resend HTTP error {e.code}: {e.read().decode()}")
            return False


# ── Provider 3: SMTP (Office365 STARTTLS or Gmail SSL) ────────────────────

def _send_via_smtp(
    smtp_email: str,
    smtp_password: str,
    smtp_host: str,
    smtp_port: int,
    recipients: List[str],
    subject: str,
    text_body: str,
    pdf_path: str,
) -> bool:
    msg            = EmailMessage()
    msg["Subject"] = subject
    msg["From"]    = smtp_email
    msg["To"]      = ", ".join(recipients)
    msg.set_content(text_body)

    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as fh:
            msg.add_attachment(
                fh.read(),
                maintype="application",
                subtype="pdf",
                filename="frontier_ai_radar_digest.pdf",
            )
        logger.info(f"PDF attached: {pdf_path}")

    try:
        if smtp_port == 587:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as s:
                s.ehlo(); s.starttls()
                s.login(smtp_email, smtp_password)
                s.send_message(msg)
        else:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as s:
                s.login(smtp_email, smtp_password)
                s.send_message(msg)
        logger.info(f"SMTP: email sent to {recipients}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP auth failed — check credentials / use App Password")
        return False
    except Exception as e:
        logger.error(f"SMTP send failed: {type(e).__name__}: {e}")
        return False


# ── Main entry point ───────────────────────────────────────────────────────

def send_digest_email(
    pdf_path: str,
    top_findings: List[Dict[str, Any]],
    recipients: List[str],
) -> bool:
    """
    Send digest email. Auto-selects provider from environment variables.
    Never raises — email failure never aborts the pipeline.
    """
    if not recipients:
        logger.info("No email recipients configured — email skipped.")
        return False

    subject   = f"🛰 Frontier AI Radar — {len(top_findings)} signals today"
    text_body = _build_text_body(top_findings)
    html_body = _build_html_body(top_findings)

    # ── Provider 1: SendGrid (sends to ANY email — recommended) ───────────
    sendgrid_key  = os.getenv("SENDGRID_API_KEY", "").strip()
    sendgrid_from = os.getenv("SENDGRID_FROM", "").strip()

    if sendgrid_key and sendgrid_key.lower() not in _PLACEHOLDERS and sendgrid_from:
        logger.info("Email: using SendGrid")
        return _send_via_sendgrid(
            sendgrid_key, sendgrid_from, recipients,
            subject, html_body, text_body, pdf_path,
        )

    # ── Provider 2: Resend (free plan: own email only unless domain verified)
    resend_key  = os.getenv("RESEND_API_KEY", "").strip()
    resend_from = os.getenv("RESEND_FROM", "AI Radar <onboarding@resend.dev>").strip()

    if resend_key and resend_key not in _PLACEHOLDERS:
        logger.info("Email: using Resend API")
        return _send_via_resend(
            resend_key, resend_from, recipients,
            subject, html_body, text_body, pdf_path,
        )

    # ── Provider 3: SMTP ──────────────────────────────────────────────────
    smtp_email    = os.getenv("SMTP_EMAIL", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_host     = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    smtp_port     = int(os.getenv("SMTP_PORT", "465"))

    if smtp_email and smtp_password and smtp_password.lower() not in _PLACEHOLDERS:
        logger.info(f"Email: using SMTP ({smtp_host}:{smtp_port})")
        return _send_via_smtp(
            smtp_email, smtp_password, smtp_host, smtp_port,
            recipients, subject, text_body, pdf_path,
        )

    # ── No provider configured ─────────────────────────────────────────────
    logger.info(
        "Email skipped — no provider configured. "
        "Add SENDGRID_API_KEY+SENDGRID_FROM to Render environment variables to enable."
    )
    return False

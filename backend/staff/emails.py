"""Email helpers for staff onboarding.
Uses the same IONOS → Resend fallback chain as core.auth_views._send_token_email.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings

logger = logging.getLogger(__name__)


def send_welcome_email(user, temp_password, login_url):
    """Send a branded welcome email to a new staff member with their login credentials."""
    brand_name = getattr(settings, 'EMAIL_BRAND_NAME', 'NBNE Business Platform')
    to_email = user.email
    to_name = user.first_name or user.username
    subject = f'Welcome to {brand_name} — Your Login Details'

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<div style="max-width:520px;margin:0 auto;padding:20px;">
  <div style="background:#0f172a;border-radius:12px 12px 0 0;padding:24px 28px;text-align:center;">
    <h1 style="margin:0;color:#f8fafc;font-size:20px;font-weight:700;">{brand_name}</h1>
  </div>
  <div style="background:#ffffff;padding:28px;border-left:1px solid #e2e8f0;border-right:1px solid #e2e8f0;">
    <h2 style="margin:0 0 12px;color:#0f172a;font-size:18px;">Welcome, {to_name}!</h2>
    <p style="margin:0 0 20px;color:#334155;font-size:15px;line-height:1.6;">Your account has been created. Use the details below to log in for the first time. You will be asked to set your own password.</p>
    <div style="background:#f1f5f9;border-radius:8px;padding:16px;margin-bottom:20px;">
      <p style="margin:0 0 8px;font-size:14px;color:#334155;"><strong>Login URL:</strong> <a href="{login_url}" style="color:#6366f1;">{login_url}</a></p>
      <p style="margin:0 0 8px;font-size:14px;color:#334155;"><strong>Email:</strong> {to_email}</p>
      <p style="margin:0;font-size:14px;color:#334155;"><strong>Temporary Password:</strong> <code style="font-size:16px;font-weight:700;color:#0f172a;">{temp_password}</code></p>
    </div>
    <div style="text-align:center;margin:24px 0;">
      <a href="{login_url}" style="display:inline-block;padding:12px 32px;background:#6366f1;color:#ffffff;text-decoration:none;border-radius:8px;font-weight:700;font-size:15px;">Log In Now</a>
    </div>
    <p style="margin:0;color:#94a3b8;font-size:13px;">If you have any questions, please contact your manager.</p>
  </div>
  <div style="background:#f1f5f9;border-radius:0 0 12px 12px;padding:16px 28px;border:1px solid #e2e8f0;border-top:none;">
    <p style="margin:0;color:#94a3b8;font-size:11px;text-align:center;">{brand_name} &middot; Secure account management</p>
  </div>
</div>
</body></html>"""

    text = (
        f"Welcome, {to_name}!\n\n"
        f"Your account has been created.\n\n"
        f"Login URL: {login_url}\n"
        f"Email: {to_email}\n"
        f"Temporary Password: {temp_password}\n\n"
        f"You will be asked to set your own password when you first log in.\n\n"
        f"If you have any questions, please contact your manager.\n\n"
        f"{brand_name}"
    )

    sent = False

    # Method 1: IONOS SMTP (reminder credentials)
    smtp_password = getattr(settings, 'REMINDER_EMAIL_HOST_PASSWORD', '')
    if smtp_password and not sent:
        try:
            host = getattr(settings, 'REMINDER_EMAIL_HOST', 'smtp.ionos.co.uk')
            port = getattr(settings, 'REMINDER_EMAIL_PORT', 465)
            use_ssl = getattr(settings, 'REMINDER_EMAIL_USE_SSL', True)
            smtp_user = getattr(settings, 'REMINDER_EMAIL_HOST_USER', '')
            from_email = getattr(settings, 'REMINDER_FROM_EMAIL', '')

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f'{brand_name} <{from_email}>'
            msg['To'] = to_email
            msg.attach(MIMEText(text, 'plain', 'utf-8'))
            msg.attach(MIMEText(html, 'html', 'utf-8'))

            if use_ssl:
                with smtplib.SMTP_SSL(host, port, timeout=15) as server:
                    server.login(smtp_user, smtp_password)
                    server.sendmail(from_email, [to_email], msg.as_string())
            else:
                with smtplib.SMTP(host, port, timeout=15) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.sendmail(from_email, [to_email], msg.as_string())
            sent = True
            logger.info(f'[STAFF] Sent welcome email via IONOS SMTP to {to_email}')
        except Exception as e:
            logger.warning(f'[STAFF] IONOS SMTP failed: {e}')

    # Method 2: Resend API
    resend_key = getattr(settings, 'RESEND_API_KEY', '')
    if resend_key and not sent:
        try:
            import resend
            resend.api_key = resend_key
            from_email = getattr(settings, 'RESEND_FROM_EMAIL', 'onboarding@resend.dev')
            resend.Emails.send({
                "from": f"{brand_name} <{from_email}>",
                "to": [to_email],
                "subject": subject,
                "html": html,
                "text": text,
            })
            sent = True
            logger.info(f'[STAFF] Sent welcome email via Resend to {to_email}')
        except Exception as e:
            logger.warning(f'[STAFF] Resend failed: {e}')

    if not sent:
        logger.error(f'[STAFF] Could not send welcome email to {to_email} — no working email provider')

    return sent

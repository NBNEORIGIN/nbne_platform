"""
Public contact form endpoint for the NBNE landing page.
Uses IONOS SMTP → Resend fallback chain.
No authentication required (public form).

Handles CORS explicitly because the landing page (business.nbne.uk)
is a different origin from the Railway backend, and the Railway
CORS_ALLOWED_ORIGINS env var may not include it.
"""
import json
import logging
import smtplib
import time
from collections import defaultdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


# Simple in-memory rate limiter: max 5 requests per 600s per IP
_rate_store = defaultdict(list)
_RATE_LIMIT = 5
_RATE_WINDOW = 600  # seconds


def _is_rate_limited(ip):
    now = time.time()
    _rate_store[ip] = [t for t in _rate_store[ip] if now - t < _RATE_WINDOW]
    if len(_rate_store[ip]) >= _RATE_LIMIT:
        return True
    _rate_store[ip].append(now)
    return False


logger = logging.getLogger(__name__)

ALLOWED_ORIGINS = [
    'https://business.nbne.uk',
    'https://nbne-landing.vercel.app',
    'http://localhost:3000',
]


def _cors_headers(request):
    """Return CORS headers if the Origin is allowed."""
    origin = request.META.get('HTTP_ORIGIN', '')
    headers = {}
    if origin in ALLOWED_ORIGINS:
        headers['Access-Control-Allow-Origin'] = origin
        headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        headers['Access-Control-Allow-Headers'] = 'Content-Type'
        headers['Access-Control-Max-Age'] = '86400'
    return headers


@csrf_exempt
def contact_form(request):
    """
    POST { name, email, phone, message }
    Sends an email to the NBNE team with the contact form details.
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        resp = JsonResponse({}, status=200)
        for k, v in _cors_headers(request).items():
            resp[k] = v
        return resp

    if request.method != 'POST':
        resp = JsonResponse({'error': 'Method not allowed'}, status=405)
        for k, v in _cors_headers(request).items():
            resp[k] = v
        return resp

    # Rate limit by IP
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')).split(',')[0].strip()
    if _is_rate_limited(ip):
        resp = JsonResponse({'error': 'Too many requests. Please try again later.'}, status=429)
        for k, v in _cors_headers(request).items():
            resp[k] = v
        return resp

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        resp = JsonResponse({'error': 'Invalid JSON'}, status=400)
        for k, v in _cors_headers(request).items():
            resp[k] = v
        return resp

    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    phone = (data.get('phone') or '').strip()
    message = (data.get('message') or '').strip()

    if not name or not email or not message:
        resp = JsonResponse({'error': 'Name, email, and message are required.'}, status=400)
        for k, v in _cors_headers(request).items():
            resp[k] = v
        return resp

    subject = f'[NBNE Contact Form] {name}'
    text_body = f"""New contact form submission from business.nbne.uk

Name:    {name}
Email:   {email}
Phone:   {phone or 'Not provided'}

Message:
{message}
"""

    to_email = 'toby@nbnesigns.com'
    sent = False

    # Method 1: IONOS SMTP (reminder credentials)
    smtp_host = getattr(settings, 'REMINDER_EMAIL_HOST', '')
    smtp_user = getattr(settings, 'REMINDER_EMAIL_HOST_USER', '')
    smtp_pass = getattr(settings, 'REMINDER_EMAIL_HOST_PASSWORD', '')
    smtp_port = getattr(settings, 'REMINDER_EMAIL_PORT', 465)
    smtp_ssl = getattr(settings, 'REMINDER_EMAIL_USE_SSL', True)
    from_email = getattr(settings, 'REMINDER_FROM_EMAIL', '') or smtp_user

    if smtp_host and smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f'NBNE Website <{from_email}>'
            msg['To'] = to_email
            msg['Reply-To'] = email
            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))

            if smtp_ssl:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=5)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=5)
                server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, [to_email], msg.as_string())
            server.quit()
            sent = True
            logger.info(f'[CONTACT] Sent contact email via IONOS SMTP from {email}')
        except Exception as e:
            logger.warning(f'[CONTACT] IONOS SMTP failed: {e}')

    # Method 2: Resend API
    resend_key = getattr(settings, 'RESEND_API_KEY', '')
    if resend_key and not sent:
        try:
            import resend
            resend.api_key = resend_key
            resend_from = getattr(settings, 'RESEND_FROM_EMAIL', 'onboarding@resend.dev')
            resend.Emails.send({
                "from": f"NBNE Website <{resend_from}>",
                "to": [to_email],
                "reply_to": email,
                "subject": subject,
                "text": text_body,
            })
            sent = True
            logger.info(f'[CONTACT] Sent contact email via Resend from {email}')
        except Exception as e:
            logger.warning(f'[CONTACT] Resend failed: {e}')

    if not sent:
        logger.error(f'[CONTACT] Could not send contact email from {email}')
        resp = JsonResponse({'error': 'Unable to send message. Please call us instead.'}, status=500)
        for k, v in _cors_headers(request).items():
            resp[k] = v
        return resp

    resp = JsonResponse({'ok': True, 'message': 'Message sent successfully.'})
    for k, v in _cors_headers(request).items():
        resp[k] = v
    return resp

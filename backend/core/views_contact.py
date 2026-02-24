"""
Public contact form endpoint for the NBNE landing page.
Uses IONOS SMTP → Resend fallback chain.
No authentication required (public form).
Rate-limited by basic throttle.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle


logger = logging.getLogger(__name__)


class ContactFormThrottle(AnonRateThrottle):
    rate = '5/hour'


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ContactFormThrottle])
def contact_form(request):
    """
    POST { name, email, phone, message }
    Sends an email to the NBNE team with the contact form details.
    """
    name = (request.data.get('name') or '').strip()
    email = (request.data.get('email') or '').strip()
    phone = (request.data.get('phone') or '').strip()
    message = (request.data.get('message') or '').strip()

    if not name or not email or not message:
        return Response(
            {'error': 'Name, email, and message are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

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
        return Response(
            {'error': 'Unable to send message. Please call us instead.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response({'ok': True, 'message': 'Message sent successfully.'})

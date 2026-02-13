"""
Booking Reminder Email System
Sends 24-hour and 1-hour reminders to clients with confirmed bookings.

Uses dedicated SMTP credentials separate from the main application email.
Falls back to Resend API if SMTP fails.

GDPR: Booking reminders are transactional (legitimate interest under Article 6(1)(f)).
No marketing consent required. No marketing content included.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import timedelta
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def _build_reminder_html(client_name, service_name, staff_name, start_time, duration, price, booking_id, is_1h=False):
    """Build a branded HTML reminder email."""
    brand_name = getattr(settings, 'EMAIL_BRAND_NAME', 'NBNE Business Platform')
    date_str = start_time.strftime('%A, %d %B %Y')
    time_str = start_time.strftime('%H:%M')
    urgency = "Your session is in 1 hour" if is_1h else "Your session is tomorrow"

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<div style="max-width:520px;margin:0 auto;padding:20px;">

  <!-- Header -->
  <div style="background:#0f172a;border-radius:12px 12px 0 0;padding:24px 28px;text-align:center;">
    <h1 style="margin:0;color:#f8fafc;font-size:20px;font-weight:700;">{brand_name}</h1>
    <p style="margin:6px 0 0;color:#94a3b8;font-size:13px;">Booking Reminder</p>
  </div>

  <!-- Body -->
  <div style="background:#ffffff;padding:28px;border-left:1px solid #e2e8f0;border-right:1px solid #e2e8f0;">
    <p style="margin:0 0 16px;color:#334155;font-size:15px;">Dear {client_name},</p>
    <p style="margin:0 0 20px;color:#334155;font-size:15px;"><strong style="color:#6366f1;">{urgency}</strong> — here are your booking details:</p>

    <!-- Booking card -->
    <div style="background:#f1f5f9;border-radius:10px;padding:20px;margin:0 0 20px;">
      <table style="width:100%;border-collapse:collapse;">
        <tr><td style="padding:6px 0;color:#64748b;font-size:13px;width:100px;">Service</td><td style="padding:6px 0;color:#0f172a;font-size:14px;font-weight:600;">{service_name}</td></tr>
        <tr><td style="padding:6px 0;color:#64748b;font-size:13px;">With</td><td style="padding:6px 0;color:#0f172a;font-size:14px;">{staff_name}</td></tr>
        <tr><td style="padding:6px 0;color:#64748b;font-size:13px;">Date</td><td style="padding:6px 0;color:#0f172a;font-size:14px;font-weight:600;">{date_str}</td></tr>
        <tr><td style="padding:6px 0;color:#64748b;font-size:13px;">Time</td><td style="padding:6px 0;color:#0f172a;font-size:14px;font-weight:600;">{time_str}</td></tr>
        <tr><td style="padding:6px 0;color:#64748b;font-size:13px;">Duration</td><td style="padding:6px 0;color:#0f172a;font-size:14px;">{duration} minutes</td></tr>
        <tr><td style="padding:6px 0;color:#64748b;font-size:13px;">Price</td><td style="padding:6px 0;color:#0f172a;font-size:14px;">&pound;{price}</td></tr>
      </table>
    </div>

    <p style="margin:0 0 8px;color:#334155;font-size:14px;">If you need to cancel or reschedule, please contact us as soon as possible.</p>
    <p style="margin:0;color:#334155;font-size:14px;">We look forward to seeing you!</p>
  </div>

  <!-- Footer -->
  <div style="background:#f1f5f9;border-radius:0 0 12px 12px;padding:20px 28px;border:1px solid #e2e8f0;border-top:none;">
    <p style="margin:0 0 6px;color:#64748b;font-size:12px;text-align:center;">{brand_name} &middot; Ref #{booking_id}</p>
    <p style="margin:0;color:#94a3b8;font-size:11px;text-align:center;">
      You are receiving this because you have an upcoming booking with {brand_name}.
      This is a service communication, not marketing.
    </p>
  </div>

</div>
</body>
</html>"""


def _build_reminder_text(client_name, service_name, staff_name, start_time, duration, price, booking_id, is_1h=False):
    """Build a plain-text fallback."""
    brand_name = getattr(settings, 'EMAIL_BRAND_NAME', 'NBNE Business Platform')
    date_str = start_time.strftime('%A, %d %B %Y')
    time_str = start_time.strftime('%H:%M')
    urgency = "Your session is in 1 hour" if is_1h else "Your session is tomorrow"

    return f"""Dear {client_name},

{urgency} - here are your booking details:

Service: {service_name}
With: {staff_name}
Date: {date_str}
Time: {time_str}
Duration: {duration} minutes
Price: £{price}
Reference: #{booking_id}

If you need to cancel or reschedule, please contact us as soon as possible.

We look forward to seeing you!

{brand_name}

---
You are receiving this because you have an upcoming booking with {brand_name}.
This is a service communication, not marketing."""


def send_reminder_email(booking, is_1h=False):
    """
    Send a reminder email for a single booking.
    Uses dedicated IONOS SMTP. Falls back to Resend API if SMTP fails.
    Returns True on success, False on failure.
    """
    client = booking.client
    service = booking.service
    staff = booking.staff

    if not client.email:
        logger.warning(f"[REMINDER] Booking #{booking.id}: client has no email, skipping")
        return False

    subject = f"Reminder: {service.name} — {'1 hour' if is_1h else 'tomorrow'} at {booking.start_time.strftime('%H:%M')}"

    html_body = _build_reminder_html(
        client_name=client.name,
        service_name=service.name,
        staff_name=staff.name,
        start_time=booking.start_time,
        duration=service.duration_minutes,
        price=str(service.price),
        booking_id=booking.id,
        is_1h=is_1h,
    )
    text_body = _build_reminder_text(
        client_name=client.name,
        service_name=service.name,
        staff_name=staff.name,
        start_time=booking.start_time,
        duration=service.duration_minutes,
        price=str(service.price),
        booking_id=booking.id,
        is_1h=is_1h,
    )

    from_email = getattr(settings, 'REMINDER_FROM_EMAIL', '')
    from_name = getattr(settings, 'EMAIL_BRAND_NAME', 'NBNE Business Platform')

    # Try SMTP first
    smtp_password = getattr(settings, 'REMINDER_EMAIL_HOST_PASSWORD', '')
    if smtp_password:
        try:
            return _send_via_smtp(from_name, from_email, client.email, subject, text_body, html_body)
        except Exception as e:
            logger.warning(f"[REMINDER] SMTP failed for booking #{booking.id}: {e}, trying Resend fallback")

    # Fallback to Resend API
    resend_key = getattr(settings, 'RESEND_API_KEY', '')
    if resend_key:
        try:
            return _send_via_resend(resend_key, from_name, from_email, client.email, subject, text_body, html_body)
        except Exception as e:
            logger.error(f"[REMINDER] Resend also failed for booking #{booking.id}: {e}")
            return False

    logger.error(f"[REMINDER] No email credentials configured — cannot send reminder for booking #{booking.id}")
    return False


def _send_via_smtp(from_name, from_email, to_email, subject, text_body, html_body):
    """Send via dedicated IONOS SMTP connection."""
    host = getattr(settings, 'REMINDER_EMAIL_HOST', 'smtp.ionos.co.uk')
    port = getattr(settings, 'REMINDER_EMAIL_PORT', 465)
    use_ssl = getattr(settings, 'REMINDER_EMAIL_USE_SSL', True)
    user = getattr(settings, 'REMINDER_EMAIL_HOST_USER', from_email)
    password = getattr(settings, 'REMINDER_EMAIL_HOST_PASSWORD', '')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f'{from_name} <{from_email}>'
    msg['To'] = to_email

    msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    if use_ssl:
        with smtplib.SMTP_SSL(host, port, timeout=15) as server:
            server.login(user, password)
            server.sendmail(from_email, [to_email], msg.as_string())
    else:
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(from_email, [to_email], msg.as_string())

    logger.info(f"[REMINDER] Sent via SMTP to {to_email}")
    return True


def _send_via_resend(api_key, from_name, from_email, to_email, subject, text_body, html_body):
    """Send via Resend HTTP API as fallback."""
    import resend
    resend.api_key = api_key

    params = {
        "from": f"{from_name} <{from_email}>",
        "to": [to_email],
        "subject": subject,
        "html": html_body,
        "text": text_body,
    }
    result = resend.Emails.send(params)
    logger.info(f"[REMINDER] Sent via Resend to {to_email}, ID: {result.get('id')}")
    return True


def process_reminders():
    """
    Main entry point: find bookings needing reminders and send them.
    Called by the management command on a schedule.
    Returns dict with counts of sent/failed.
    """
    from .models import Booking

    now = timezone.now()
    results = {'sent_24h': 0, 'sent_1h': 0, 'failed': 0, 'skipped': 0}

    # ── 24-hour reminders ──
    # Window: bookings starting between 23h and 25h from now (to handle 10-min cron intervals)
    window_24h_start = now + timedelta(hours=23)
    window_24h_end = now + timedelta(hours=25)

    bookings_24h = Booking.objects.filter(
        start_time__gte=window_24h_start,
        start_time__lte=window_24h_end,
        status__in=['confirmed', 'pending'],
        reminder_sent_24h=False,
    ).select_related('client', 'service', 'staff')

    for booking in bookings_24h:
        if not booking.client.email:
            results['skipped'] += 1
            continue
        success = send_reminder_email(booking, is_1h=False)
        if success:
            booking.reminder_sent_24h = True
            booking.save(update_fields=['reminder_sent_24h'])
            results['sent_24h'] += 1
        else:
            results['failed'] += 1

    # ── 1-hour reminders ──
    # Window: bookings starting between 50min and 70min from now
    window_1h_start = now + timedelta(minutes=50)
    window_1h_end = now + timedelta(minutes=70)

    bookings_1h = Booking.objects.filter(
        start_time__gte=window_1h_start,
        start_time__lte=window_1h_end,
        status__in=['confirmed', 'pending'],
        reminder_sent_1h=False,
    ).select_related('client', 'service', 'staff')

    for booking in bookings_1h:
        if not booking.client.email:
            results['skipped'] += 1
            continue
        success = send_reminder_email(booking, is_1h=True)
        if success:
            booking.reminder_sent_1h = True
            booking.save(update_fields=['reminder_sent_1h'])
            results['sent_1h'] += 1
        else:
            results['failed'] += 1

    return results

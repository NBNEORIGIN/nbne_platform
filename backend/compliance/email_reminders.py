"""
Compliance diary reminder emails.
Sends weekly digest emails to tenant owners/managers about:
- Overdue compliance items (legal first, then best practice)
- Items due within the next 30 days
- Upcoming renewals (expiry_date approaching)

Uses the same SMTP/Resend fallback chain as booking reminders.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def _build_html(tenant_name, score, overdue_items, due_soon_items, compliant_count, total_count):
    """Build branded HTML digest email."""
    brand = tenant_name or 'Your Business'

    overdue_rows = ''
    for item in overdue_items:
        badge = '<span style="background:#dc2626;color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:700;">LEGAL</span>' if item['item_type'] == 'LEGAL' else '<span style="background:#2563eb;color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:700;">Best Practice</span>'
        overdue_rows += f'''
        <tr>
            <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;">
                <strong>{item['title']}</strong><br>
                <span style="color:#6b7280;font-size:13px;">{item['category']} · {item.get('frequency_type', 'annual')}</span>
            </td>
            <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;">{badge}</td>
            <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;color:#dc2626;font-weight:600;">
                {item.get('days_overdue', 0)} days overdue
            </td>
        </tr>'''

    due_soon_rows = ''
    for item in due_soon_items:
        badge = '<span style="background:#dc2626;color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:700;">LEGAL</span>' if item['item_type'] == 'LEGAL' else '<span style="background:#2563eb;color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:700;">Best Practice</span>'
        due_soon_rows += f'''
        <tr>
            <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;">
                <strong>{item['title']}</strong><br>
                <span style="color:#6b7280;font-size:13px;">{item['category']} · {item.get('frequency_type', 'annual')}</span>
            </td>
            <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;">{badge}</td>
            <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;color:#d97706;font-weight:600;">
                Due in {item.get('days_until', '?')} days
            </td>
        </tr>'''

    # Score colour
    if score >= 80:
        score_color = '#16a34a'
        score_label = 'Compliant'
    elif score >= 60:
        score_color = '#d97706'
        score_label = 'Attention Needed'
    else:
        score_color = '#dc2626'
        score_label = 'Action Required'

    overdue_section = ''
    if overdue_rows:
        overdue_section = f'''
        <div style="margin-bottom:24px;">
            <h2 style="color:#dc2626;font-size:16px;margin:0 0 12px;">⚠ Overdue Items ({len(overdue_items)})</h2>
            <table style="width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;border:1px solid #e5e7eb;">
                <thead>
                    <tr style="background:#fef2f2;">
                        <th style="padding:10px 12px;text-align:left;font-size:13px;color:#6b7280;">Item</th>
                        <th style="padding:10px 12px;text-align:left;font-size:13px;color:#6b7280;">Type</th>
                        <th style="padding:10px 12px;text-align:left;font-size:13px;color:#6b7280;">Status</th>
                    </tr>
                </thead>
                <tbody>{overdue_rows}</tbody>
            </table>
        </div>'''

    due_soon_section = ''
    if due_soon_rows:
        due_soon_section = f'''
        <div style="margin-bottom:24px;">
            <h2 style="color:#d97706;font-size:16px;margin:0 0 12px;">📅 Due Soon ({len(due_soon_items)})</h2>
            <table style="width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;border:1px solid #e5e7eb;">
                <thead>
                    <tr style="background:#fffbeb;">
                        <th style="padding:10px 12px;text-align:left;font-size:13px;color:#6b7280;">Item</th>
                        <th style="padding:10px 12px;text-align:left;font-size:13px;color:#6b7280;">Type</th>
                        <th style="padding:10px 12px;text-align:left;font-size:13px;color:#6b7280;">When</th>
                    </tr>
                </thead>
                <tbody>{due_soon_rows}</tbody>
            </table>
        </div>'''

    return f'''<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<div style="max-width:600px;margin:0 auto;padding:24px;">
    <div style="background:#111827;color:#fff;padding:20px 24px;border-radius:12px 12px 0 0;text-align:center;">
        <h1 style="margin:0;font-size:20px;font-weight:700;">Health &amp; Safety Compliance Digest</h1>
        <p style="margin:6px 0 0;color:#9ca3af;font-size:14px;">{brand}</p>
    </div>
    <div style="background:#fff;padding:24px;border-radius:0 0 12px 12px;border:1px solid #e5e7eb;border-top:none;">
        <div style="text-align:center;margin-bottom:24px;">
            <div style="display:inline-block;width:100px;height:100px;border-radius:50%;border:6px solid {score_color};line-height:88px;text-align:center;font-size:32px;font-weight:800;color:{score_color};">{score}</div>
            <div style="margin-top:8px;font-size:14px;color:{score_color};font-weight:600;">{score_label}</div>
            <div style="margin-top:4px;font-size:13px;color:#6b7280;">{compliant_count} of {total_count} items compliant</div>
        </div>

        {overdue_section}
        {due_soon_section}

        <div style="text-align:center;margin-top:24px;">
            <p style="color:#6b7280;font-size:13px;margin:0 0 12px;">Log in to your dashboard to resolve these items and keep your business compliant.</p>
        </div>
    </div>
    <div style="text-align:center;padding:16px;color:#9ca3af;font-size:12px;">
        This is an automated compliance reminder from {brand}.<br>
        You are receiving this because you are an owner or manager.
    </div>
</div>
</body>
</html>'''


def _build_text(tenant_name, score, overdue_items, due_soon_items, compliant_count, total_count):
    """Build plain-text fallback."""
    brand = tenant_name or 'Your Business'
    lines = [
        f'Health & Safety Compliance Digest — {brand}',
        f'Peace of Mind Score: {score}%',
        f'{compliant_count} of {total_count} items compliant',
        '',
    ]
    if overdue_items:
        lines.append(f'OVERDUE ({len(overdue_items)} items):')
        for item in overdue_items:
            typ = 'LEGAL' if item['item_type'] == 'LEGAL' else 'Best Practice'
            lines.append(f'  - {item["title"]} [{typ}] — {item.get("days_overdue", 0)} days overdue')
        lines.append('')
    if due_soon_items:
        lines.append(f'DUE SOON ({len(due_soon_items)} items):')
        for item in due_soon_items:
            typ = 'LEGAL' if item['item_type'] == 'LEGAL' else 'Best Practice'
            lines.append(f'  - {item["title"]} [{typ}] — due in {item.get("days_until", "?")} days')
        lines.append('')
    lines.append('Log in to your dashboard to resolve these items.')
    lines.append(f'\n---\nAutomated compliance reminder from {brand}.')
    return '\n'.join(lines)


def _send_via_smtp(from_name, from_email, to_email, subject, text_body, html_body):
    """Send via SMTP (same pattern as booking reminders)."""
    host = getattr(settings, 'REMINDER_EMAIL_HOST', getattr(settings, 'EMAIL_HOST', 'smtp.ionos.co.uk'))
    port = int(getattr(settings, 'REMINDER_EMAIL_PORT', getattr(settings, 'EMAIL_PORT', 465)))
    use_ssl = str(getattr(settings, 'REMINDER_EMAIL_USE_SSL', 'True')).lower() in ('true', '1', 'yes')
    user = getattr(settings, 'REMINDER_EMAIL_HOST_USER', getattr(settings, 'EMAIL_HOST_USER', from_email))
    password = getattr(settings, 'REMINDER_EMAIL_HOST_PASSWORD', getattr(settings, 'EMAIL_HOST_PASSWORD', ''))

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

    logger.info(f"[COMPLIANCE-REMINDER] Sent via SMTP to {to_email}")
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
    logger.info(f"[COMPLIANCE-REMINDER] Sent via Resend to {to_email}, ID: {result.get('id')}")
    return True


def send_compliance_digest(tenant, to_email, tenant_name, score, overdue_items, due_soon_items, compliant_count, total_count):
    """Send a single compliance digest email."""
    subject_parts = []
    if overdue_items:
        subject_parts.append(f'{len(overdue_items)} overdue')
    if due_soon_items:
        subject_parts.append(f'{len(due_soon_items)} due soon')
    if not subject_parts:
        return False  # Nothing to report

    subject = f'H&S Compliance: {", ".join(subject_parts)} — {tenant_name}'

    html_body = _build_html(tenant_name, score, overdue_items, due_soon_items, compliant_count, total_count)
    text_body = _build_text(tenant_name, score, overdue_items, due_soon_items, compliant_count, total_count)

    from_email = getattr(settings, 'REMINDER_FROM_EMAIL', getattr(settings, 'DEFAULT_FROM_EMAIL', ''))
    from_name = tenant_name or getattr(settings, 'EMAIL_BRAND_NAME', 'NBNE Business Platform')

    # Try SMTP first
    smtp_password = getattr(settings, 'REMINDER_EMAIL_HOST_PASSWORD', getattr(settings, 'EMAIL_HOST_PASSWORD', ''))
    if smtp_password:
        try:
            return _send_via_smtp(from_name, from_email, to_email, subject, text_body, html_body)
        except Exception as e:
            logger.warning(f"[COMPLIANCE-REMINDER] SMTP failed for {to_email}: {e}")

    # Fallback to Resend
    resend_key = getattr(settings, 'RESEND_API_KEY', '')
    if resend_key:
        try:
            return _send_via_resend(resend_key, from_name, from_email, to_email, subject, text_body, html_body)
        except Exception as e:
            logger.error(f"[COMPLIANCE-REMINDER] Resend also failed for {to_email}: {e}")
            return False

    logger.error(f"[COMPLIANCE-REMINDER] No email credentials configured")
    return False


def process_compliance_reminders():
    """
    Main entry point: iterate all tenants, find overdue/due-soon items,
    send digest emails to owners and managers.
    Returns dict with counts.
    """
    from tenants.models import TenantSettings
    from .models import ComplianceItem, ComplianceCategory, PeaceOfMindScore

    today = timezone.now().date()
    results = {'tenants_checked': 0, 'emails_sent': 0, 'emails_failed': 0, 'tenants_skipped': 0}

    for tenant in TenantSettings.objects.all():
        results['tenants_checked'] += 1

        items = list(ComplianceItem.objects.select_related('category').filter(category__tenant=tenant))
        if not items:
            results['tenants_skipped'] += 1
            continue

        overdue_items = []
        due_soon_items = []
        compliant_count = 0

        for item in items:
            effective_date = item.expiry_date or item.next_due_date
            if item.status == 'OVERDUE':
                days_overdue = (today - effective_date).days if effective_date and effective_date < today else 0
                overdue_items.append({
                    'title': item.title,
                    'item_type': item.item_type,
                    'category': item.category.name,
                    'frequency_type': item.frequency_type,
                    'days_overdue': days_overdue,
                })
            elif item.status == 'DUE_SOON':
                days_until = (effective_date - today).days if effective_date else 0
                due_soon_items.append({
                    'title': item.title,
                    'item_type': item.item_type,
                    'category': item.category.name,
                    'frequency_type': item.frequency_type,
                    'days_until': days_until,
                })
            else:
                compliant_count += 1

        # Skip if nothing to report
        if not overdue_items and not due_soon_items:
            results['tenants_skipped'] += 1
            continue

        # Sort: legal items first, then by urgency
        overdue_items.sort(key=lambda x: (0 if x['item_type'] == 'LEGAL' else 1, -x.get('days_overdue', 0)))
        due_soon_items.sort(key=lambda x: (0 if x['item_type'] == 'LEGAL' else 1, x.get('days_until', 999)))

        # Get score
        score_obj = PeaceOfMindScore.objects.filter(tenant=tenant).first()
        score = score_obj.score if score_obj else 0

        tenant_name = tenant.business_name or tenant.slug

        # Find owner/manager emails for this tenant
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            recipients = User.objects.filter(
                tenant=tenant,
                is_active=True,
                role__in=['owner', 'manager'],
            ).exclude(email='').values_list('email', flat=True).distinct()

            for email in recipients:
                success = send_compliance_digest(
                    tenant, email, tenant_name, score,
                    overdue_items, due_soon_items,
                    compliant_count, len(items),
                )
                if success:
                    results['emails_sent'] += 1
                else:
                    results['emails_failed'] += 1
        except Exception as e:
            logger.error(f"[COMPLIANCE-REMINDER] Error processing tenant {tenant.slug}: {e}")
            results['emails_failed'] += 1

    return results

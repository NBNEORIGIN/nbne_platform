"""
Global Command Bar — deterministic command router.

Single endpoint: POST /api/command/
Body: { "text": "Jordan is sick today" }

Returns: { "success": true, "message": "Jordan marked sick today", "action": "mark_sick", "navigate": "/admin/staff" }

No AI. Keyword matching only. Calls existing backend functions directly.
"""
import re
from datetime import date, timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


# ─── Staff name resolver ───

def _resolve_staff(tenant, text_lower):
    """Find a staff member whose first name or display_name appears in the text."""
    try:
        from staff.models import StaffProfile
        profiles = StaffProfile.objects.filter(tenant=tenant, is_active=True).select_related('user')
        for p in profiles:
            first = p.user.first_name.strip().lower()
            display = p.display_name.strip().lower()
            if display and display in text_lower:
                return p
            if first and len(first) >= 2 and first in text_lower:
                return p
    except Exception:
        pass
    return None


# ─── Value extractor ───

def _extract_value(text):
    """Extract £ value from text like 'John Smith £120' → 12000 pence."""
    m = re.search(r'[£$](\d+(?:\.\d{1,2})?)', text)
    if m:
        return int(float(m.group(1)) * 100)
    return 0


def _extract_name_after(text, marker):
    """Extract a name after a marker word. E.g. 'Add new lead John Smith £120' → 'John Smith'"""
    idx = text.lower().find(marker.lower())
    if idx < 0:
        return None
    rest = text[idx + len(marker):].strip()
    # Remove £value if present
    rest = re.sub(r'[£$]\d+(?:\.\d{1,2})?', '', rest).strip()
    # Take remaining words as name (max 4 words)
    words = rest.split()[:4]
    return ' '.join(words).strip() if words else None


# ─── Command handlers ───

def _cmd_mark_sick(tenant, text_lower, text):
    """Mark staff member as sick today."""
    staff = _resolve_staff(tenant, text_lower)
    if not staff:
        return {'success': False, 'message': 'Could not find staff member. Try: "Jordan is sick today"'}

    from staff.models import AbsenceRecord
    today = date.today()
    _, created = AbsenceRecord.objects.get_or_create(
        staff=staff, date=today, record_type='ABSENCE',
        defaults={'reason': 'Sick — logged via command bar', 'is_authorised': True}
    )
    if created:
        return {'success': True, 'message': f'{staff.display_name} marked sick today', 'action': 'mark_sick', 'navigate': '/admin/staff'}
    return {'success': True, 'message': f'{staff.display_name} was already marked sick today', 'action': 'mark_sick', 'navigate': '/admin/staff'}


def _cmd_who_is_off(tenant, text_lower, text):
    """List staff off today (absences + approved leave)."""
    today = date.today()
    off_names = []

    try:
        from staff.models import AbsenceRecord, LeaveRequest
        absences = AbsenceRecord.objects.filter(staff__tenant=tenant, date=today).select_related('staff')
        for a in absences:
            off_names.append(f'{a.staff.display_name} (sick/absent)')

        leaves = LeaveRequest.objects.filter(
            staff__tenant=tenant, status='APPROVED',
            start_date__lte=today, end_date__gte=today
        ).select_related('staff')
        for lv in leaves:
            off_names.append(f'{lv.staff.display_name} (leave)')
    except Exception:
        pass

    if not off_names:
        return {'success': True, 'message': 'No staff off today', 'action': 'who_off', 'data': []}
    return {'success': True, 'message': f'{len(off_names)} staff off today: {", ".join(off_names)}', 'action': 'who_off', 'data': off_names}


def _cmd_show_issues(tenant, text_lower, text):
    """Load today's dashboard issues."""
    return {'success': True, 'message': 'Showing today\'s issues', 'action': 'show_issues', 'navigate': '/admin'}


def _cmd_show_vip_clients(tenant, text_lower, text):
    """Filter clients with lifetime_value > £20."""
    try:
        from bookings.models import Client
        vips = Client.objects.filter(tenant=tenant, lifetime_value__gt=20).order_by('-lifetime_value')[:20]
        data = [{'name': c.name, 'email': c.email, 'lifetime_value': float(c.lifetime_value)} for c in vips]
        return {'success': True, 'message': f'{len(data)} VIP clients found', 'action': 'show_vip', 'data': data, 'navigate': '/admin/clients'}
    except Exception as e:
        return {'success': False, 'message': f'Error: {e}'}


def _cmd_show_at_risk(tenant, text_lower, text):
    """Clients with no booking in 90 days."""
    try:
        from bookings.models import Client, Booking
        from django.db.models import Max
        cutoff = timezone.now() - timedelta(days=90)
        clients_with_recent = Booking.objects.filter(
            tenant=tenant, start_time__gte=cutoff
        ).values_list('client_id', flat=True).distinct()
        at_risk = Client.objects.filter(tenant=tenant).exclude(id__in=clients_with_recent).order_by('-lifetime_value')[:20]
        data = [{'name': c.name, 'email': c.email, 'lifetime_value': float(c.lifetime_value)} for c in at_risk]
        return {'success': True, 'message': f'{len(data)} at-risk clients (no booking in 90 days)', 'action': 'show_at_risk', 'data': data}
    except Exception as e:
        return {'success': False, 'message': f'Error: {e}'}


def _cmd_export_vip(tenant, text_lower, text):
    """Trigger VIP client CSV export."""
    return {'success': True, 'message': 'Exporting VIP clients...', 'action': 'export_vip', 'navigate': '/api/django/crm/leads/export/?status=CONVERTED'}


def _cmd_add_lead(tenant, text_lower, text):
    """Create a new CRM lead from command text."""
    from crm.models import Lead, LeadHistory

    # Try to extract name: "add lead John Smith £120" or "new lead John Smith"
    name = None
    for marker in ['add new lead ', 'add lead ', 'new lead ']:
        name = _extract_name_after(text, marker)
        if name:
            break
    if not name:
        # Fallback: everything after "lead"
        name = _extract_name_after(text, 'lead')
    if not name:
        return {'success': False, 'message': 'Could not parse lead name. Try: "Add new lead John Smith £120"'}

    value = _extract_value(text)
    lead = Lead.objects.create(
        tenant=tenant, name=name, source='manual', status='NEW', value_pence=value,
        notes='Created via command bar',
    )
    LeadHistory.objects.create(lead=lead, action='Lead created', detail=f'Via command bar: "{text}"')
    val_str = f' (£{value/100:.0f})' if value else ''
    return {'success': True, 'message': f'Lead added: {name}{val_str}', 'action': 'add_lead', 'navigate': '/admin/clients'}


def _cmd_show_bookings_today(tenant, text_lower, text):
    """Show today's bookings."""
    return {'success': True, 'message': 'Showing today\'s bookings', 'action': 'show_bookings', 'navigate': '/admin/bookings'}


def _cmd_show_unassigned(tenant, text_lower, text):
    """Show unassigned bookings."""
    try:
        from bookings.models import Booking
        today = date.today()
        unassigned = Booking.objects.filter(
            tenant=tenant, start_time__date__gte=today, staff__isnull=True
        ).count()
        return {'success': True, 'message': f'{unassigned} unassigned booking(s)', 'action': 'show_unassigned', 'navigate': '/admin/bookings'}
    except Exception:
        return {'success': True, 'message': 'Showing unassigned bookings', 'action': 'show_unassigned', 'navigate': '/admin/bookings'}


def _cmd_compliance_status(tenant, text_lower, text):
    """Show compliance overview."""
    return {'success': True, 'message': 'Showing compliance status', 'action': 'compliance_status', 'navigate': '/admin/health-safety'}


def _cmd_compliance_overdue(tenant, text_lower, text):
    """Show overdue compliance items."""
    try:
        from compliance.models import ComplianceItem
        overdue = ComplianceItem.objects.filter(category__tenant=tenant, status='OVERDUE').count()
        return {'success': True, 'message': f'{overdue} overdue compliance item(s)', 'action': 'compliance_overdue', 'navigate': '/admin/health-safety'}
    except Exception:
        return {'success': True, 'message': 'Showing overdue compliance', 'action': 'compliance_overdue', 'navigate': '/admin/health-safety'}


# ─── Command map: ordered list of (keywords, handler) ───
# Checked top-to-bottom, first match wins. More specific patterns first.

COMMAND_MAP = [
    # Staff
    (['sick', 'off sick', 'called in sick', 'unwell', 'ill today'], _cmd_mark_sick),
    (['who is off', 'who\'s off', 'whos off', 'staff off'], _cmd_who_is_off),

    # Dashboard
    (['today\'s issues', 'todays issues', 'show issues', 'sorted issues', 'show sorted'], _cmd_show_issues),

    # CRM / Clients
    (['add new lead', 'add lead', 'new lead'], _cmd_add_lead),
    (['export vip', 'export clients'], _cmd_export_vip),
    (['vip client', 'vip customers', 'show vip'], _cmd_show_vip_clients),
    (['at risk', 'at-risk', 'atrisk', 'no booking'], _cmd_show_at_risk),

    # Bookings
    (['unassigned booking', 'show unassigned'], _cmd_show_unassigned),
    (['today\'s booking', 'todays booking', 'show booking', 'show today'], _cmd_show_bookings_today),

    # Compliance
    (['overdue compliance', 'show overdue'], _cmd_compliance_overdue),
    (['compliance status', 'compliance overview', 'show compliance', 'h&s', 'health and safety'], _cmd_compliance_status),
]

# Suggestions shown in the dropdown
SUGGESTIONS = [
    {'text': 'Jordan is sick today', 'category': 'Staff'},
    {'text': 'Who is off today', 'category': 'Staff'},
    {'text': 'Show today\'s issues', 'category': 'Dashboard'},
    {'text': 'Show VIP clients', 'category': 'Clients'},
    {'text': 'Show at-risk clients', 'category': 'Clients'},
    {'text': 'Export VIP clients', 'category': 'Clients'},
    {'text': 'Add new lead John Smith £120', 'category': 'CRM'},
    {'text': 'Show today\'s bookings', 'category': 'Bookings'},
    {'text': 'Show unassigned bookings', 'category': 'Bookings'},
    {'text': 'Show compliance status', 'category': 'Compliance'},
    {'text': 'Show overdue compliance', 'category': 'Compliance'},
]


# ─── Main endpoint ───

@api_view(['POST'])
@permission_classes([AllowAny])
def execute_command(request):
    """
    POST /api/command/
    Body: { "text": "Jordan is sick today" }
    """
    tenant = getattr(request, 'tenant', None)
    text = request.data.get('text', '').strip()

    if not text:
        return Response({'success': False, 'message': 'Type a command'}, status=status.HTTP_400_BAD_REQUEST)

    text_lower = text.lower()

    # Match command
    for keywords, handler in COMMAND_MAP:
        for kw in keywords:
            if kw in text_lower:
                result = handler(tenant, text_lower, text)
                return Response(result)

    # No match
    return Response({
        'success': False,
        'message': 'Command not recognised',
        'suggestions': [
            'Jordan is sick today',
            'Show VIP clients',
            'Show today\'s issues',
            'Add new lead John Smith £120',
        ],
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def command_suggestions(request):
    """GET /api/command/suggestions/ — Return all available command suggestions."""
    q = request.query_params.get('q', '').lower().strip()
    if q:
        filtered = [s for s in SUGGESTIONS if q in s['text'].lower()]
        return Response(filtered[:8])
    return Response(SUGGESTIONS)

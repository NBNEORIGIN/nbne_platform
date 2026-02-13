"""
Phase 7 — Dashboard Intelligence API (Visual Dashboard v2)
GET /api/dashboard-summary/
POST /api/backfill-sbe/
"""
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count, Q, F, Avg
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Booking, Client, Service
from .models_availability import TimesheetEntry, LeaveRequest


@api_view(['POST'])
@permission_classes([AllowAny])
def backfill_sbe(request):
    """POST /api/backfill-sbe/ — Trigger SBE backfill for unscored bookings"""
    from .smart_engine import update_reliability_score, calculate_booking_risk, generate_booking_recommendation
    bookings = Booking.objects.filter(risk_score__isnull=True).select_related('client', 'service')
    results = []
    for b in bookings:
        try:
            update_reliability_score(b.client)
            calculate_booking_risk(b)
            generate_booking_recommendation(b)
            results.append({'id': b.id, 'status': 'ok', 'risk': b.risk_score, 'level': b.risk_level})
        except Exception as e:
            results.append({'id': b.id, 'status': 'error', 'error': f'{type(e).__name__}: {e}'})
    return Response({'backfilled': len([r for r in results if r['status'] == 'ok']), 'results': results})


def _revenue_breakdown(today_start, week_end):
    """Calculate secured / deposit / at-risk revenue breakdown."""
    upcoming = Booking.objects.filter(
        start_time__gte=today_start,
        start_time__lt=week_end,
        status__in=['confirmed', 'completed', 'pending']
    ).select_related('service')

    total = Decimal('0')
    secured = Decimal('0')
    deposit = Decimal('0')
    at_risk = Decimal('0')

    bookings_breakdown = []
    for b in upcoming:
        price = b.service.price or Decimal('0')
        total += price

        if b.payment_status == 'paid':
            secured += price
            cat = 'secured'
        elif b.recommended_deposit_percent and b.recommended_deposit_percent >= 100:
            secured += price
            cat = 'secured'
        elif b.recommended_deposit_percent and b.recommended_deposit_percent > 0:
            dep_amount = price * Decimal(str(b.recommended_deposit_percent / 100))
            deposit += dep_amount
            at_risk += price - dep_amount
            cat = 'deposit'
        else:
            at_risk += price
            cat = 'at_risk'

        bookings_breakdown.append({
            'id': b.id,
            'client_name': b.client.name if b.client_id else '',
            'service_name': b.service.name,
            'price': float(price),
            'risk_level': b.risk_level or '',
            'category': cat,
            'start_time': b.start_time.isoformat(),
        })

    return {
        'total': float(total),
        'secured': float(secured),
        'deposit': float(deposit),
        'at_risk': float(at_risk),
        'bookings': bookings_breakdown,
    }


def _client_quadrant():
    """Build client quadrant data: reliability vs booking frequency."""
    ninety_days_ago = timezone.now() - timedelta(days=90)
    clients = Client.objects.all()
    points = []
    for c in clients:
        freq = Booking.objects.filter(
            client=c,
            start_time__gte=ninety_days_ago,
            status__in=['confirmed', 'completed']
        ).count()
        rel = c.reliability_score or 0

        if rel >= 60 and freq >= 2:
            zone = 'VIP'
        elif rel >= 60:
            zone = 'Stable'
        elif freq >= 2:
            zone = 'Watch'
        else:
            zone = 'High Risk'

        points.append({
            'id': c.id,
            'name': c.name,
            'email': c.email,
            'reliability': round(rel, 1),
            'frequency': freq,
            'zone': zone,
            'total_bookings': c.total_bookings,
            'no_shows': c.no_show_count,
            'lifetime_value': float(c.lifetime_value or 0),
        })
    return points


def _demand_calendar():
    """Build demand calendar: hour x day_of_week grid with no-show rates."""
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    # Booking counts by hour and dow
    booking_data = (
        Booking.objects.filter(
            start_time__gte=thirty_days_ago,
            status__in=['confirmed', 'completed', 'no_show']
        )
        .extra(select={
            'hour': 'EXTRACT(hour FROM start_time)',
            'dow': 'EXTRACT(dow FROM start_time)',
        })
        .values('hour', 'dow')
        .annotate(
            total=Count('id'),
            no_shows=Count('id', filter=Q(status='no_show')),
        )
    )

    # Service demand indices
    services = list(Service.objects.filter(active=True).values('id', 'name', 'demand_index', 'off_peak_discount_allowed'))

    cells = []
    for entry in booking_data:
        h = int(entry['hour'])
        d = int(entry['dow'])
        t = entry['total']
        ns = entry['no_shows']
        ns_rate = round(ns / t * 100, 1) if t > 0 else 0
        cells.append({
            'hour': h,
            'day_of_week': d,
            'total_bookings': t,
            'no_shows': ns,
            'no_show_rate': ns_rate,
            'demand_intensity': min(100, t * 20),
        })

    return {'cells': cells, 'services': services}


def _generate_owner_actions(today_start, today_end):
    """Generate top actionable recommendations for the owner."""
    actions = []

    # 1. Critical risk bookings today
    critical = Booking.objects.filter(
        start_time__gte=today_start,
        start_time__lt=today_end,
        risk_level='CRITICAL',
        status__in=['confirmed', 'pending']
    ).select_related('client', 'service')
    for b in critical[:2]:
        actions.append({
            'severity': 'critical',
            'message': f'{b.client.name} — {b.service.name} is CRITICAL risk. Recommend full prepayment.',
            'link': f'/admin/bookings',
            'booking_id': b.id,
        })

    # 2. High risk bookings this week
    week_end = today_start + timedelta(days=7)
    high_risk = Booking.objects.filter(
        start_time__gte=today_start,
        start_time__lt=week_end,
        risk_level='HIGH',
        status__in=['confirmed', 'pending']
    ).select_related('client', 'service')
    hr_count = high_risk.count()
    if hr_count > 0:
        total_at_risk = high_risk.aggregate(t=Sum('revenue_at_risk'))['t'] or 0
        actions.append({
            'severity': 'high',
            'message': f'{hr_count} high-risk booking{"s" if hr_count != 1 else ""} this week — £{float(total_at_risk):.0f} revenue at risk.',
            'link': '/admin/bookings',
        })

    # 3. Clients with consecutive no-shows
    repeat_offenders = Client.objects.filter(consecutive_no_shows__gte=2).order_by('-consecutive_no_shows')[:2]
    for c in repeat_offenders:
        actions.append({
            'severity': 'warning',
            'message': f'{c.name} has {c.consecutive_no_shows} consecutive no-shows. Consider requiring full prepayment.',
            'link': '/admin/clients',
        })

    # 4. Off-peak slots with low demand
    low_demand_services = Service.objects.filter(active=True, demand_index__lt=20, off_peak_discount_allowed=True)
    for s in low_demand_services[:1]:
        actions.append({
            'severity': 'info',
            'message': f'"{s.name}" has low demand (index {s.demand_index:.0f}). Consider an off-peak discount to boost bookings.',
            'link': '/admin/services',
        })

    # 5. Unscored bookings
    unscored = Booking.objects.filter(risk_score__isnull=True, status__in=['confirmed', 'pending']).count()
    if unscored > 0:
        actions.append({
            'severity': 'info',
            'message': f'{unscored} booking{"s" if unscored != 1 else ""} not yet scored by the engine. Run backfill.',
            'link': '/admin/bookings',
        })

    return actions[:5]


@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_summary(request):
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    week_end = today_start + timedelta(days=7)

    # Revenue breakdown
    revenue = _revenue_breakdown(today_start, week_end)

    # Revenue today only
    today_bookings = Booking.objects.filter(
        start_time__gte=today_start,
        start_time__lt=today_end,
        status__in=['confirmed', 'completed']
    )
    revenue_today = float(today_bookings.aggregate(total=Sum('service__price'))['total'] or 0)

    # High risk bookings today
    high_risk_today = Booking.objects.filter(
        start_time__gte=today_start,
        start_time__lt=today_end,
        risk_level__in=['HIGH', 'CRITICAL'],
        status__in=['confirmed', 'pending']
    ).count()

    # Reliability distribution
    clients = Client.objects.all()
    reliability_dist = {
        'excellent': clients.filter(reliability_score__gte=85).count(),
        'good': clients.filter(reliability_score__gte=60, reliability_score__lt=85).count(),
        'fair': clients.filter(reliability_score__gte=40, reliability_score__lt=60).count(),
        'poor': clients.filter(reliability_score__lt=40).count(),
    }

    total_upcoming = Booking.objects.filter(
        start_time__gte=today_start,
        status__in=['confirmed', 'pending']
    ).count()

    avg_reliability = clients.aggregate(avg=Avg('reliability_score'))['avg'] or 0

    # Client quadrant
    client_quadrant = _client_quadrant()

    # Demand calendar
    demand_calendar = _demand_calendar()

    # Owner actions
    owner_actions = _generate_owner_actions(today_start, today_end)

    # Staff hours this month (real-time from timesheets)
    from datetime import date as dt_date
    month_start = dt_date(now.year, now.month, 1)
    ts_qs = TimesheetEntry.objects.filter(
        date__gte=month_start,
        date__lte=now.date(),
    ).exclude(notes__contains='avail-demo').select_related('staff_member')

    staff_hours = {}
    for entry in ts_qs:
        sid = entry.staff_member_id
        if sid not in staff_hours:
            staff_hours[sid] = {
                'staff_id': sid,
                'staff_name': entry.staff_member.name,
                'scheduled_hours': 0,
                'actual_hours': 0,
            }
        staff_hours[sid]['scheduled_hours'] += entry.scheduled_hours or 0
        staff_hours[sid]['actual_hours'] += entry.actual_hours or 0

    staff_hours_list = sorted(staff_hours.values(), key=lambda r: r['staff_name'])
    for r in staff_hours_list:
        r['scheduled_hours'] = round(r['scheduled_hours'], 1)
        r['actual_hours'] = round(r['actual_hours'], 1)

    total_scheduled = round(sum(r['scheduled_hours'] for r in staff_hours_list), 1)
    total_actual = round(sum(r['actual_hours'] for r in staff_hours_list), 1)

    # Leave this week (approved + requested, overlapping next 7 days)
    leave_qs = LeaveRequest.objects.filter(
        start_datetime__date__lte=week_end.date(),
        end_datetime__date__gte=today_start.date(),
        status__in=['APPROVED', 'REQUESTED'],
    ).exclude(reason__contains='avail-demo').select_related('staff_member').order_by('start_datetime')

    leave_this_week = []
    for lv in leave_qs:
        days = max(1, (lv.end_datetime.date() - lv.start_datetime.date()).days)
        leave_this_week.append({
            'id': lv.id,
            'staff_id': lv.staff_member_id,
            'staff_name': lv.staff_member.name,
            'leave_type': lv.leave_type,
            'start_date': lv.start_datetime.date().isoformat(),
            'end_date': lv.end_datetime.date().isoformat(),
            'days': days,
            'status': lv.status,
            'reason': lv.reason,
        })

    return Response({
        'revenue_today': revenue_today,
        'revenue_next_7_days': revenue['total'],
        'revenue_breakdown': revenue,
        'high_risk_bookings_today': high_risk_today,
        'reliability_distribution': reliability_dist,
        'client_quadrant': client_quadrant,
        'demand_calendar': demand_calendar,
        'owner_actions': owner_actions,
        'total_upcoming_bookings': total_upcoming,
        'average_reliability_score': round(float(avg_reliability), 1),
        'staff_hours_this_month': {
            'month': month_start.strftime('%Y-%m'),
            'total_scheduled': total_scheduled,
            'total_actual': total_actual,
            'staff': staff_hours_list,
        },
        'leave_this_week': leave_this_week,
    })

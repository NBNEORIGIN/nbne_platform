"""
Smart Booking Engine v1
Phases 2-5: Reliability, Risk, Recommendation, Demand Intelligence
Phase 6+8: Logging all decisions to OptimisationLog
"""
import logging
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.db.models import Avg, Count, Q

logger = logging.getLogger(__name__)


# ============================================================
# PHASE 2 — Reliability Engine
# ============================================================

def update_reliability_score(client):
    """
    Recalculate client reliability score based on booking history.
    Called when booking is completed, no-show, or cancelled.
    """
    from .models import Booking

    all_bookings = Booking.objects.filter(client=client)
    total = all_bookings.count()
    completed = all_bookings.filter(status='completed').count()
    cancelled = all_bookings.filter(status='cancelled').count()
    no_shows = all_bookings.filter(status='no_show').count()

    # Update counters
    client.total_bookings = total
    client.completed_bookings = completed
    client.cancelled_bookings = cancelled
    client.no_show_count = no_shows

    # Calculate consecutive no-shows (from most recent bookings)
    recent = all_bookings.order_by('-start_time')[:10]
    consecutive = 0
    for b in recent:
        if b.status == 'no_show':
            consecutive += 1
        else:
            break
    client.consecutive_no_shows = consecutive

    # Last no-show date
    last_ns = all_bookings.filter(status='no_show').order_by('-start_time').first()
    if last_ns:
        client.last_no_show_date = last_ns.start_time

    # Base reliability formula
    if total > 0:
        base = (completed / total) * 100
    else:
        base = 100.0

    penalty = (no_shows * 10) + (consecutive * 5)
    score = base - penalty

    # Weight recent 90-day behaviour higher
    ninety_days_ago = timezone.now() - timedelta(days=90)
    recent_bookings = all_bookings.filter(start_time__gte=ninety_days_ago)
    recent_total = recent_bookings.count()
    if recent_total >= 2:
        recent_completed = recent_bookings.filter(status='completed').count()
        recent_no_shows = recent_bookings.filter(status='no_show').count()
        recent_score = ((recent_completed / recent_total) * 100) - (recent_no_shows * 15)
        # Blend: 60% recent, 40% overall
        score = (recent_score * 0.6) + (score * 0.4)

    # Clamp 0-100
    client.reliability_score = max(0.0, min(100.0, score))

    # Lifetime value
    from django.db.models import Sum
    total_value = all_bookings.filter(
        status__in=['completed', 'confirmed']
    ).aggregate(total=Sum('service__price'))['total'] or 0
    client.lifetime_value = Decimal(str(total_value))

    # Average days between bookings
    completed_dates = list(
        all_bookings.filter(status__in=['completed', 'confirmed'])
        .order_by('start_time')
        .values_list('start_time', flat=True)
    )
    if len(completed_dates) >= 2:
        gaps = [(completed_dates[i+1] - completed_dates[i]).days for i in range(len(completed_dates)-1)]
        client.avg_days_between_bookings = sum(gaps) / len(gaps)

    client.save()

    logger.info(
        f"[SBE] Reliability updated: client={client.id} score={client.reliability_score:.1f} "
        f"total={total} completed={completed} no_shows={no_shows} consecutive={consecutive}"
    )
    return client.reliability_score


# ============================================================
# PHASE 3 — Booking Risk Engine
# ============================================================

def calculate_booking_risk(booking):
    """
    Calculate risk score for a booking based on client reliability,
    service value, and demand.
    """
    client = booking.client
    service = booking.service

    reliability = client.reliability_score
    demand = service.demand_index  # 0-100
    service_price = float(service.price)

    # Service value factor: normalise price to 0-100 scale
    # Assume max service price ~£500 for normalisation
    service_value_factor = min(100, (service_price / 500) * 100)

    # Risk formula v1
    risk_score = (
        (100 - reliability) * 0.6 +
        demand * 0.2 +
        service_value_factor * 0.2
    )
    risk_score = max(0, min(100, risk_score))

    # Risk level
    if risk_score <= 25:
        risk_level = 'LOW'
    elif risk_score <= 50:
        risk_level = 'MEDIUM'
    elif risk_score <= 75:
        risk_level = 'HIGH'
    else:
        risk_level = 'CRITICAL'

    # Revenue at risk = service price if deposit < 100%
    deposit_pct = service.deposit_percentage or 0
    if deposit_pct < 100:
        revenue_at_risk = Decimal(str(service_price)) * Decimal(str((100 - deposit_pct) / 100))
    else:
        revenue_at_risk = Decimal('0')

    booking.risk_score = risk_score
    booking.risk_level = risk_level
    booking.revenue_at_risk = revenue_at_risk
    booking.save(update_fields=['risk_score', 'risk_level', 'revenue_at_risk'])

    logger.info(
        f"[SBE] Risk calculated: booking={booking.id} score={risk_score:.1f} "
        f"level={risk_level} revenue_at_risk=£{revenue_at_risk:.2f}"
    )
    return risk_score, risk_level, revenue_at_risk


# ============================================================
# PHASE 4 — Smart Recommendation Engine
# ============================================================

def generate_booking_recommendation(booking):
    """
    Generate payment/pricing recommendations based on risk profile.
    Returns recommendation dict and stores in booking.
    """
    client = booking.client
    service = booking.service
    reliability = client.reliability_score
    risk_level = booking.risk_level or 'MEDIUM'
    demand = service.demand_index

    rec = {
        'recommended_payment_type': 'deposit',
        'recommended_deposit_percent': 50.0,
        'recommended_price_adjustment': 0,
        'recommended_incentive': '',
        'allow_booking': True,
        'explanation': [],
    }

    # Rule 1: High reliability → low deposit
    if reliability > 85:
        rec['recommended_deposit_percent'] = 10.0
        rec['explanation'].append(f'Reliable client (score {reliability:.0f}) — 10% deposit recommended')

    # Rule 2: Low reliability → high deposit
    elif reliability < 60:
        rec['recommended_deposit_percent'] = max(50.0, 100 - reliability)
        rec['explanation'].append(f'Low reliability (score {reliability:.0f}) — {rec["recommended_deposit_percent"]:.0f}% deposit recommended')

    # Rule 3: Consecutive no-shows → full payment
    if client.consecutive_no_shows >= 2:
        rec['recommended_payment_type'] = 'full'
        rec['recommended_deposit_percent'] = 100.0
        rec['explanation'].append(f'{client.consecutive_no_shows} consecutive no-shows — full upfront payment recommended')

    # Rule 4: CRITICAL risk → flag for manual review
    if risk_level == 'CRITICAL':
        rec['allow_booking'] = False
        rec['explanation'].append('CRITICAL risk level — manual review recommended')

    # Rule 5: Off-peak discount for reliable clients
    is_off_peak = demand < 30
    if is_off_peak and reliability > 70 and service.off_peak_discount_allowed:
        discount_pct = min(15, max(5, (reliability - 70) / 2))
        rec['recommended_price_adjustment'] = -round(float(service.price) * discount_pct / 100, 2)
        rec['recommended_incentive'] = f'{discount_pct:.0f}% off-peak discount'
        rec['explanation'].append(f'Off-peak slot + reliable client — {discount_pct:.0f}% discount suggested')

    # Rule 6: Peak + low reliability → increase deposit
    is_peak = demand > 70
    if is_peak and reliability < 60:
        rec['recommended_deposit_percent'] = min(100, rec['recommended_deposit_percent'] + 20)
        rec['explanation'].append(f'Peak demand + low reliability — deposit increased to {rec["recommended_deposit_percent"]:.0f}%')

    # Store in booking
    explanation_text = '; '.join(rec['explanation']) if rec['explanation'] else 'Standard recommendation'
    booking.recommended_payment_type = rec['recommended_payment_type']
    booking.recommended_deposit_percent = rec['recommended_deposit_percent']
    booking.recommended_price_adjustment = Decimal(str(rec['recommended_price_adjustment']))
    booking.recommended_incentive = rec['recommended_incentive']
    booking.recommendation_reason = explanation_text

    # Optimisation snapshot
    snapshot = {
        'engine_version': 'v1',
        'timestamp': timezone.now().isoformat(),
        'inputs': {
            'reliability_score': reliability,
            'risk_score': booking.risk_score,
            'risk_level': risk_level,
            'demand_index': demand,
            'service_price': float(service.price),
            'consecutive_no_shows': client.consecutive_no_shows,
            'total_bookings': client.total_bookings,
        },
        'outputs': {
            'recommended_payment_type': rec['recommended_payment_type'],
            'recommended_deposit_percent': rec['recommended_deposit_percent'],
            'recommended_price_adjustment': rec['recommended_price_adjustment'],
            'recommended_incentive': rec['recommended_incentive'],
            'allow_booking': rec['allow_booking'],
        },
        'explanation': rec['explanation'],
    }
    booking.optimisation_snapshot = snapshot
    booking.save(update_fields=[
        'recommended_payment_type', 'recommended_deposit_percent',
        'recommended_price_adjustment', 'recommended_incentive',
        'recommendation_reason', 'optimisation_snapshot',
    ])

    # Phase 8: Log to OptimisationLog
    _log_decision(booking, snapshot)

    logger.info(
        f"[SBE] Recommendation: booking={booking.id} deposit={rec['recommended_deposit_percent']}% "
        f"allow={rec['allow_booking']} reason={explanation_text}"
    )
    return rec


# ============================================================
# PHASE 5 — Demand Intelligence
# ============================================================

def update_service_demand_index():
    """
    Calculate demand index for each service based on booking frequency.
    Should be run daily (management command or cron).
    """
    from .models import Service, Booking

    thirty_days_ago = timezone.now() - timedelta(days=30)

    services = Service.objects.filter(active=True)
    if not services.exists():
        return

    # Get booking counts per service in last 30 days
    demand_data = (
        Booking.objects.filter(
            start_time__gte=thirty_days_ago,
            status__in=['confirmed', 'completed', 'pending']
        )
        .values('service_id')
        .annotate(count=Count('id'))
    )
    counts = {d['service_id']: d['count'] for d in demand_data}

    # Find max for normalisation
    max_count = max(counts.values()) if counts else 1

    for service in services:
        count = counts.get(service.id, 0)
        # Normalise 0-100
        demand_index = (count / max_count) * 100 if max_count > 0 else 0

        # Factor in time-of-day patterns (hour distribution)
        hour_bookings = (
            Booking.objects.filter(
                service=service,
                start_time__gte=thirty_days_ago,
                status__in=['confirmed', 'completed']
            )
            .extra(select={'hour': 'EXTRACT(hour FROM start_time)'})
            .values('hour')
            .annotate(count=Count('id'))
        )
        # Peak hours: if bookings cluster in certain hours, demand is higher
        if hour_bookings:
            hour_counts = [h['count'] for h in hour_bookings]
            peak_concentration = max(hour_counts) / sum(hour_counts) if sum(hour_counts) > 0 else 0
            # Boost demand if bookings are concentrated (peak pattern)
            demand_index = demand_index * (1 + peak_concentration * 0.3)

        service.demand_index = min(100, max(0, demand_index))
        service.save(update_fields=['demand_index'])

        logger.info(f"[SBE] Demand updated: service={service.id} '{service.name}' index={service.demand_index:.1f}")


# ============================================================
# PHASE 6+8 — Logging
# ============================================================

def _log_decision(booking, snapshot):
    """Log algorithm decision to OptimisationLog for R&D evidence."""
    from .models import OptimisationLog

    OptimisationLog.objects.create(
        booking=booking,
        input_data=snapshot.get('inputs'),
        output_recommendation=snapshot.get('outputs'),
        override_applied=booking.override_applied,
        override_reason=booking.override_reason,
        reliability_score=snapshot['inputs'].get('reliability_score'),
        risk_score=snapshot['inputs'].get('risk_score'),
    )


def log_override(booking, reason):
    """Log when owner overrides a recommendation."""
    from .models import OptimisationLog

    booking.override_applied = True
    booking.override_reason = reason
    booking.save(update_fields=['override_applied', 'override_reason'])

    OptimisationLog.objects.create(
        booking=booking,
        input_data=booking.optimisation_snapshot.get('inputs') if booking.optimisation_snapshot else None,
        output_recommendation=booking.optimisation_snapshot.get('outputs') if booking.optimisation_snapshot else None,
        override_applied=True,
        override_reason=reason,
        reliability_score=booking.client.reliability_score,
        risk_score=booking.risk_score,
    )
    logger.info(f"[SBE] Override logged: booking={booking.id} reason={reason}")


# ============================================================
# ORCHESTRATOR — Run full pipeline on a booking
# ============================================================

def process_booking(booking):
    """
    Run the full Smart Booking Engine pipeline on a booking:
    1. Update client reliability
    2. Calculate booking risk
    3. Generate recommendation
    """
    update_reliability_score(booking.client)
    calculate_booking_risk(booking)
    generate_booking_recommendation(booking)
    return booking


def on_booking_status_change(booking, old_status, new_status):
    """
    Trigger reliability recalculation when booking status changes.
    Called from booking cancel/complete/no-show actions.
    """
    if new_status in ('completed', 'cancelled', 'no_show'):
        # Reset consecutive no-shows on completed booking
        if new_status == 'completed':
            booking.client.consecutive_no_shows = 0
            booking.client.save(update_fields=['consecutive_no_shows'])

        update_reliability_score(booking.client)
        logger.info(
            f"[SBE] Status change: booking={booking.id} {old_status}->{new_status} "
            f"client reliability={booking.client.reliability_score:.1f}"
        )

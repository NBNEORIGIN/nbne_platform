"""
Deterministic Cover Logic

Suggests cover candidates for sick/absent staff using configurable strategy:
- 7-day rotation (default): round-robin based on last cover date
- Tiered: ordered by seniority or predefined tier

Rules:
- Must show WHY a person is suggested
- If declined → log COVER_DECLINED, suggest next candidate
- Never auto-assign — owner always confirms
"""
from datetime import timedelta
from django.utils import timezone


def get_cover_candidates(absent_staff_id, service=None, strategy='rotation', max_candidates=3):
    """
    Return ordered list of cover candidates with reasons.

    Each candidate:
    {
        'staff_id': int,
        'name': str,
        'reason': str,
        'rank': int,
    }
    """
    from bookings.models import Staff as BookingStaff

    base_qs = BookingStaff.objects.filter(active=True).exclude(id=absent_staff_id)

    # Filter by service qualification if provided
    if service:
        base_qs = base_qs.filter(services=service)

    if strategy == 'rotation':
        return _rotation_candidates(base_qs, max_candidates)
    elif strategy == 'tiered':
        return _tiered_candidates(base_qs, max_candidates)
    else:
        return _rotation_candidates(base_qs, max_candidates)


def _rotation_candidates(staff_qs, max_candidates):
    """
    7-day rotation: prefer staff who haven't covered recently.
    Uses BusinessEvent log to determine last cover date per staff member.
    """
    from core.models_events import BusinessEvent

    seven_days_ago = timezone.now() - timedelta(days=7)

    # Get recent cover events to determine who covered last
    recent_covers = BusinessEvent.objects.filter(
        event_type='COVER_ACCEPTED',
        created_at__gte=seven_days_ago,
    ).values_list('payload', flat=True)

    # Extract staff IDs who covered recently
    recently_covered_ids = set()
    for payload in recent_covers:
        if isinstance(payload, dict) and 'cover_staff_id' in payload:
            recently_covered_ids.add(payload['cover_staff_id'])

    candidates = []
    rank = 1

    # First: staff who haven't covered in 7 days
    for staff in staff_qs.order_by('name'):
        if staff.id not in recently_covered_ids and rank <= max_candidates:
            candidates.append({
                'staff_id': staff.id,
                'name': staff.name,
                'reason': f'Next in 7-day rotation and available',
                'rank': rank,
            })
            rank += 1

    # Then: staff who have covered recently (if we need more)
    if rank <= max_candidates:
        for staff in staff_qs.order_by('name'):
            if staff.id in recently_covered_ids and rank <= max_candidates:
                candidates.append({
                    'staff_id': staff.id,
                    'name': staff.name,
                    'reason': f'Available (covered recently — last 7 days)',
                    'rank': rank,
                })
                rank += 1

    return candidates[:max_candidates]


def _tiered_candidates(staff_qs, max_candidates):
    """
    Tiered: order by staff ID (proxy for seniority — can be replaced
    with an explicit tier field later).
    """
    candidates = []
    for rank, staff in enumerate(staff_qs.order_by('id')[:max_candidates], start=1):
        candidates.append({
            'staff_id': staff.id,
            'name': staff.name,
            'reason': f'Tier {rank} — seniority order',
            'rank': rank,
        })
    return candidates


def get_next_candidate(absent_staff_id, declined_staff_ids, service=None, strategy='rotation'):
    """
    After a decline, get the next candidate excluding already-declined staff.
    """
    from bookings.models import Staff as BookingStaff

    base_qs = BookingStaff.objects.filter(active=True).exclude(
        id=absent_staff_id
    ).exclude(id__in=declined_staff_ids)

    if service:
        base_qs = base_qs.filter(services=service)

    candidates = _rotation_candidates(base_qs, 1) if strategy == 'rotation' else _tiered_candidates(base_qs, 1)
    return candidates[0] if candidates else None

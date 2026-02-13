"""
Staff Availability Engine — Service Module
Computes real-time staff availability from working patterns, overrides, leave, and blocks.
Designed to power booking slot generation for UK small businesses.

Usage:
    from bookings.availability import get_staff_availability, get_free_slots

    # Get available time ranges for a staff member on a date
    ranges = get_staff_availability(staff_id=1, target_date=date(2025, 3, 10))
    # => [(time(9, 0), time(12, 0)), (time(13, 0), time(17, 0))]

    # Get bookable slots (subtracting existing bookings)
    slots = get_free_slots(staff_id=1, target_date=date(2025, 3, 10), slot_minutes=60)
    # => [datetime(..., 9, 0), datetime(..., 10, 0), ...]
"""
import zoneinfo
from datetime import date, time, datetime, timedelta
from typing import List, Tuple, Optional

from django.db.models import Q
from django.utils import timezone as django_tz

from .models_availability import (
    WorkingPattern, WorkingPatternRule,
    AvailabilityOverride, AvailabilityOverridePeriod,
    LeaveRequest, BlockedTime,
)

TimeRange = Tuple[time, time]
UK_TZ = zoneinfo.ZoneInfo('Europe/London')


# ─────────────────────────────────────────────────────────────────────
# Range helpers (pure functions, no DB)
# ─────────────────────────────────────────────────────────────────────

def normalize_ranges(ranges: List[TimeRange]) -> List[TimeRange]:
    """Sort and filter out empty/invalid ranges."""
    valid = [(s, e) for s, e in ranges if s < e]
    return sorted(valid, key=lambda r: r[0])


def merge_overlaps(ranges: List[TimeRange]) -> List[TimeRange]:
    """Merge overlapping or adjacent time ranges into a minimal set."""
    if not ranges:
        return []
    sorted_r = normalize_ranges(ranges)
    merged: List[TimeRange] = [sorted_r[0]]
    for start, end in sorted_r[1:]:
        prev_start, prev_end = merged[-1]
        if start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))
    return merged


def subtract_ranges(
    base: List[TimeRange], removals: List[TimeRange]
) -> List[TimeRange]:
    """Subtract removal ranges from base ranges. Returns remaining ranges."""
    if not base or not removals:
        return list(base)

    base = merge_overlaps(base)
    removals = merge_overlaps(removals)
    result: List[TimeRange] = []

    for b_start, b_end in base:
        current_start = b_start
        for r_start, r_end in removals:
            if r_end <= current_start:
                continue
            if r_start >= b_end:
                break
            # There is overlap
            if r_start > current_start:
                result.append((current_start, r_start))
            current_start = max(current_start, r_end)
        if current_start < b_end:
            result.append((current_start, b_end))

    return result


def union_ranges(a: List[TimeRange], b: List[TimeRange]) -> List[TimeRange]:
    """Union two sets of time ranges."""
    return merge_overlaps(list(a) + list(b))


def _datetime_to_local_time(dt: datetime) -> time:
    """Convert a tz-aware datetime to Europe/London local time."""
    local = dt.astimezone(UK_TZ)
    return local.time()


def _date_to_aware_datetime(target_date: date, t: time) -> datetime:
    """Combine date + time into a tz-aware datetime in Europe/London."""
    naive = datetime.combine(target_date, t)
    return naive.replace(tzinfo=UK_TZ)


# ─────────────────────────────────────────────────────────────────────
# Core availability computation
# ─────────────────────────────────────────────────────────────────────

def _get_active_pattern(staff_id: int, target_date: date) -> Optional[WorkingPattern]:
    """Find the active working pattern for a staff member on a given date."""
    patterns = WorkingPattern.objects.filter(
        staff_member_id=staff_id,
        is_active=True,
    ).order_by('-effective_from')

    for p in patterns:
        if p.effective_from and p.effective_from > target_date:
            continue
        if p.effective_to and p.effective_to < target_date:
            continue
        return p
    return None


def _get_base_ranges(staff_id: int, target_date: date) -> List[TimeRange]:
    """Get base weekly availability from WorkingPatternRules for the weekday."""
    pattern = _get_active_pattern(staff_id, target_date)
    if not pattern:
        return []

    weekday = target_date.weekday()  # 0=Mon, 6=Sun
    rules = WorkingPatternRule.objects.filter(
        working_pattern=pattern,
        weekday=weekday,
    ).order_by('sort_order', 'start_time')

    return [(r.start_time, r.end_time) for r in rules]


def _apply_overrides(
    staff_id: int, target_date: date, base: List[TimeRange]
) -> List[TimeRange]:
    """Apply AvailabilityOverride for the date."""
    try:
        override = AvailabilityOverride.objects.get(
            staff_member_id=staff_id, date=target_date
        )
    except AvailabilityOverride.DoesNotExist:
        return base

    if override.mode == 'CLOSED':
        return []

    periods = list(
        override.periods.all().order_by('sort_order', 'start_time')
    )
    override_ranges: List[TimeRange] = [(p.start_time, p.end_time) for p in periods]

    if override.mode == 'REPLACE':
        return merge_overlaps(override_ranges)
    elif override.mode == 'ADD':
        return union_ranges(base, override_ranges)
    elif override.mode == 'REMOVE':
        return subtract_ranges(base, override_ranges)

    return base


def _subtract_leave(
    staff_id: int, target_date: date, ranges: List[TimeRange]
) -> List[TimeRange]:
    """Subtract APPROVED leave overlaps from availability."""
    if not ranges:
        return []

    day_start = _date_to_aware_datetime(target_date, time(0, 0))
    day_end = _date_to_aware_datetime(target_date, time(23, 59, 59))

    leaves = LeaveRequest.objects.filter(
        staff_member_id=staff_id,
        status='APPROVED',
        start_datetime__lt=day_end,
        end_datetime__gt=day_start,
    )

    leave_ranges: List[TimeRange] = []
    for lv in leaves:
        lv_start = _datetime_to_local_time(lv.start_datetime)
        lv_end = _datetime_to_local_time(lv.end_datetime)

        # If leave spans the entire day
        if lv.start_datetime <= day_start and lv.end_datetime >= day_end:
            return []

        # If leave starts before this day, clip to midnight
        if lv.start_datetime <= day_start:
            lv_start = time(0, 0)
        # If leave ends after this day, clip to end of day
        if lv.end_datetime >= day_end:
            lv_end = time(23, 59, 59)

        if lv_start < lv_end:
            leave_ranges.append((lv_start, lv_end))

    return subtract_ranges(ranges, leave_ranges)


def _subtract_blocks(
    staff_id: int, target_date: date, ranges: List[TimeRange]
) -> List[TimeRange]:
    """Subtract BlockedTime overlaps (staff-specific + global)."""
    if not ranges:
        return []

    day_start = _date_to_aware_datetime(target_date, time(0, 0))
    day_end = _date_to_aware_datetime(target_date, time(23, 59, 59))

    blocks = BlockedTime.objects.filter(
        Q(staff_member_id=staff_id) | Q(staff_member__isnull=True),
        start_datetime__lt=day_end,
        end_datetime__gt=day_start,
    )

    block_ranges: List[TimeRange] = []
    for bl in blocks:
        bl_start = _datetime_to_local_time(bl.start_datetime)
        bl_end = _datetime_to_local_time(bl.end_datetime)

        if bl.start_datetime <= day_start:
            bl_start = time(0, 0)
        if bl.end_datetime >= day_end:
            bl_end = time(23, 59, 59)

        if bl_start < bl_end:
            block_ranges.append((bl_start, bl_end))

    return subtract_ranges(ranges, block_ranges)


def get_staff_availability(
    staff_id: int, target_date: date
) -> List[TimeRange]:
    """
    Compute final availability for a staff member on a given date.

    Precedence:
    1. Base from active WorkingPatternRules for the weekday
    2. Apply AvailabilityOverride (CLOSED / REPLACE / ADD / REMOVE)
    3. Subtract APPROVED LeaveRequest overlaps
    4. Subtract BlockedTime overlaps (staff-specific + global)

    Returns list of (start_time, end_time) tuples in Europe/London local time.
    """
    # 1. Base weekly pattern
    ranges = _get_base_ranges(staff_id, target_date)

    # 2. Apply overrides
    ranges = _apply_overrides(staff_id, target_date, ranges)

    # 3. Subtract leave
    ranges = _subtract_leave(staff_id, target_date, ranges)

    # 4. Subtract blocks
    ranges = _subtract_blocks(staff_id, target_date, ranges)

    return merge_overlaps(ranges)


# ─────────────────────────────────────────────────────────────────────
# Booking slot generation
# ─────────────────────────────────────────────────────────────────────

def get_free_slots(
    staff_id: int,
    target_date: date,
    slot_minutes: int = 60,
    existing_bookings_qs=None,
) -> List[dict]:
    """
    Compute bookable time slots for a staff member on a date.

    1. Get availability ranges from get_staff_availability()
    2. Subtract existing bookings for that day
    3. Generate slot start times at 15-minute intervals within remaining ranges

    Returns list of dicts: [{'start': datetime, 'end': datetime}, ...]
    All datetimes are tz-aware in Europe/London.
    """
    availability = get_staff_availability(staff_id, target_date)
    if not availability:
        return []

    # Convert existing bookings to local time ranges
    booking_ranges: List[TimeRange] = []
    if existing_bookings_qs is not None:
        day_start_dt = _date_to_aware_datetime(target_date, time(0, 0))
        day_end_dt = _date_to_aware_datetime(target_date, time(23, 59, 59))
        bookings = existing_bookings_qs.filter(
            staff_id=staff_id,
            start_time__lt=day_end_dt,
            end_time__gt=day_start_dt,
            status__in=['pending', 'confirmed'],
        )
        for bk in bookings:
            bk_start = _datetime_to_local_time(bk.start_time)
            bk_end = _datetime_to_local_time(bk.end_time)
            if bk_start < bk_end:
                booking_ranges.append((bk_start, bk_end))
    else:
        # Default: query from Booking model
        from .models import Booking
        day_start_dt = _date_to_aware_datetime(target_date, time(0, 0))
        day_end_dt = _date_to_aware_datetime(target_date, time(23, 59, 59))
        bookings = Booking.objects.filter(
            staff_id=staff_id,
            start_time__lt=day_end_dt,
            end_time__gt=day_start_dt,
            status__in=['pending', 'confirmed'],
        )
        for bk in bookings:
            bk_start = _datetime_to_local_time(bk.start_time)
            bk_end = _datetime_to_local_time(bk.end_time)
            if bk_start < bk_end:
                booking_ranges.append((bk_start, bk_end))

    # Subtract bookings from availability
    free_ranges = subtract_ranges(availability, booking_ranges)
    if not free_ranges:
        return []

    # Generate slots at 15-minute intervals
    slot_delta = timedelta(minutes=slot_minutes)
    interval = timedelta(minutes=15)
    slots = []

    for range_start, range_end in free_ranges:
        range_start_dt = _date_to_aware_datetime(target_date, range_start)
        range_end_dt = _date_to_aware_datetime(target_date, range_end)

        current = range_start_dt
        while current + slot_delta <= range_end_dt:
            slots.append({
                'start': current.isoformat(),
                'end': (current + slot_delta).isoformat(),
            })
            current += interval

    return slots

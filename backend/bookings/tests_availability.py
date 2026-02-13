"""
Staff Availability Engine — Unit Tests
Tests for range helpers (union, subtract, merge) and override mode logic.
"""
from datetime import time, date, datetime, timedelta
from django.test import TestCase

from .availability import (
    normalize_ranges, merge_overlaps, subtract_ranges, union_ranges,
    get_staff_availability, get_free_slots,
    _date_to_aware_datetime, UK_TZ,
)
from .models import Staff
from .models_availability import (
    WorkingPattern, WorkingPatternRule,
    AvailabilityOverride, AvailabilityOverridePeriod,
    LeaveRequest, BlockedTime,
)


# ─────────────────────────────────────────────────────────────────────
# Pure range helper tests (no DB)
# ─────────────────────────────────────────────────────────────────────

class NormalizeRangesTest(TestCase):
    def test_empty(self):
        self.assertEqual(normalize_ranges([]), [])

    def test_filters_invalid(self):
        self.assertEqual(
            normalize_ranges([(time(10, 0), time(9, 0))]),
            [],
        )

    def test_sorts(self):
        self.assertEqual(
            normalize_ranges([(time(14, 0), time(17, 0)), (time(9, 0), time(12, 0))]),
            [(time(9, 0), time(12, 0)), (time(14, 0), time(17, 0))],
        )


class MergeOverlapsTest(TestCase):
    def test_empty(self):
        self.assertEqual(merge_overlaps([]), [])

    def test_no_overlap(self):
        ranges = [(time(9, 0), time(12, 0)), (time(13, 0), time(17, 0))]
        self.assertEqual(merge_overlaps(ranges), ranges)

    def test_adjacent(self):
        ranges = [(time(9, 0), time(12, 0)), (time(12, 0), time(17, 0))]
        self.assertEqual(merge_overlaps(ranges), [(time(9, 0), time(17, 0))])

    def test_overlapping(self):
        ranges = [(time(9, 0), time(13, 0)), (time(11, 0), time(17, 0))]
        self.assertEqual(merge_overlaps(ranges), [(time(9, 0), time(17, 0))])

    def test_contained(self):
        ranges = [(time(9, 0), time(17, 0)), (time(10, 0), time(12, 0))]
        self.assertEqual(merge_overlaps(ranges), [(time(9, 0), time(17, 0))])

    def test_multiple_merges(self):
        ranges = [
            (time(9, 0), time(10, 0)),
            (time(10, 0), time(11, 0)),
            (time(14, 0), time(15, 0)),
            (time(14, 30), time(16, 0)),
        ]
        self.assertEqual(merge_overlaps(ranges), [
            (time(9, 0), time(11, 0)),
            (time(14, 0), time(16, 0)),
        ])


class SubtractRangesTest(TestCase):
    def test_empty_base(self):
        self.assertEqual(subtract_ranges([], [(time(9, 0), time(10, 0))]), [])

    def test_empty_removals(self):
        base = [(time(9, 0), time(17, 0))]
        self.assertEqual(subtract_ranges(base, []), base)

    def test_no_overlap(self):
        base = [(time(9, 0), time(12, 0))]
        removals = [(time(13, 0), time(14, 0))]
        self.assertEqual(subtract_ranges(base, removals), base)

    def test_full_removal(self):
        base = [(time(9, 0), time(12, 0))]
        removals = [(time(8, 0), time(13, 0))]
        self.assertEqual(subtract_ranges(base, removals), [])

    def test_split_in_middle(self):
        base = [(time(9, 0), time(17, 0))]
        removals = [(time(12, 0), time(13, 0))]
        self.assertEqual(subtract_ranges(base, removals), [
            (time(9, 0), time(12, 0)),
            (time(13, 0), time(17, 0)),
        ])

    def test_trim_start(self):
        base = [(time(9, 0), time(17, 0))]
        removals = [(time(8, 0), time(10, 0))]
        self.assertEqual(subtract_ranges(base, removals), [
            (time(10, 0), time(17, 0)),
        ])

    def test_trim_end(self):
        base = [(time(9, 0), time(17, 0))]
        removals = [(time(16, 0), time(18, 0))]
        self.assertEqual(subtract_ranges(base, removals), [
            (time(9, 0), time(16, 0)),
        ])

    def test_multiple_removals_from_split_shift(self):
        base = [(time(9, 0), time(12, 0)), (time(14, 0), time(18, 0))]
        removals = [(time(10, 0), time(11, 0)), (time(15, 0), time(16, 0))]
        self.assertEqual(subtract_ranges(base, removals), [
            (time(9, 0), time(10, 0)),
            (time(11, 0), time(12, 0)),
            (time(14, 0), time(15, 0)),
            (time(16, 0), time(18, 0)),
        ])


class UnionRangesTest(TestCase):
    def test_disjoint(self):
        a = [(time(9, 0), time(12, 0))]
        b = [(time(14, 0), time(17, 0))]
        self.assertEqual(union_ranges(a, b), [
            (time(9, 0), time(12, 0)),
            (time(14, 0), time(17, 0)),
        ])

    def test_overlapping(self):
        a = [(time(9, 0), time(13, 0))]
        b = [(time(12, 0), time(17, 0))]
        self.assertEqual(union_ranges(a, b), [(time(9, 0), time(17, 0))])


# ─────────────────────────────────────────────────────────────────────
# Integration tests (with DB)
# ─────────────────────────────────────────────────────────────────────

class GetStaffAvailabilityTest(TestCase):
    def setUp(self):
        self.staff = Staff.objects.create(
            name='Test Therapist', email='test@example.com', phone='07000000000'
        )
        self.pattern = WorkingPattern.objects.create(
            staff_member=self.staff, name='Default', is_active=True
        )
        # Mon-Fri 9-12, 13-17 (split shift)
        for day in range(5):
            WorkingPatternRule.objects.create(
                working_pattern=self.pattern, weekday=day,
                start_time=time(9, 0), end_time=time(12, 0), sort_order=0,
            )
            WorkingPatternRule.objects.create(
                working_pattern=self.pattern, weekday=day,
                start_time=time(13, 0), end_time=time(17, 0), sort_order=1,
            )

    def test_base_weekday(self):
        # 2025-03-10 is a Monday
        result = get_staff_availability(self.staff.id, date(2025, 3, 10))
        self.assertEqual(result, [
            (time(9, 0), time(12, 0)),
            (time(13, 0), time(17, 0)),
        ])

    def test_base_weekend_empty(self):
        # 2025-03-09 is a Sunday (weekday=6), no rules
        result = get_staff_availability(self.staff.id, date(2025, 3, 9))
        self.assertEqual(result, [])

    def test_override_closed(self):
        AvailabilityOverride.objects.create(
            staff_member=self.staff, date=date(2025, 3, 10), mode='CLOSED',
            reason='Bank holiday',
        )
        result = get_staff_availability(self.staff.id, date(2025, 3, 10))
        self.assertEqual(result, [])

    def test_override_replace(self):
        override = AvailabilityOverride.objects.create(
            staff_member=self.staff, date=date(2025, 3, 10), mode='REPLACE',
        )
        AvailabilityOverridePeriod.objects.create(
            availability_override=override,
            start_time=time(10, 0), end_time=time(14, 0),
        )
        result = get_staff_availability(self.staff.id, date(2025, 3, 10))
        self.assertEqual(result, [(time(10, 0), time(14, 0))])

    def test_override_add(self):
        override = AvailabilityOverride.objects.create(
            staff_member=self.staff, date=date(2025, 3, 10), mode='ADD',
        )
        # Add evening hours
        AvailabilityOverridePeriod.objects.create(
            availability_override=override,
            start_time=time(18, 0), end_time=time(20, 0),
        )
        result = get_staff_availability(self.staff.id, date(2025, 3, 10))
        self.assertEqual(result, [
            (time(9, 0), time(12, 0)),
            (time(13, 0), time(17, 0)),
            (time(18, 0), time(20, 0)),
        ])

    def test_override_remove(self):
        override = AvailabilityOverride.objects.create(
            staff_member=self.staff, date=date(2025, 3, 10), mode='REMOVE',
        )
        # Remove 10-11 from the morning shift
        AvailabilityOverridePeriod.objects.create(
            availability_override=override,
            start_time=time(10, 0), end_time=time(11, 0),
        )
        result = get_staff_availability(self.staff.id, date(2025, 3, 10))
        self.assertEqual(result, [
            (time(9, 0), time(10, 0)),
            (time(11, 0), time(12, 0)),
            (time(13, 0), time(17, 0)),
        ])

    def test_leave_blocks_availability(self):
        # Approved leave covering morning
        LeaveRequest.objects.create(
            staff_member=self.staff,
            leave_type='ANNUAL',
            start_datetime=_date_to_aware_datetime(date(2025, 3, 10), time(0, 0)),
            end_datetime=_date_to_aware_datetime(date(2025, 3, 10), time(12, 30)),
            status='APPROVED',
        )
        result = get_staff_availability(self.staff.id, date(2025, 3, 10))
        self.assertEqual(result, [(time(13, 0), time(17, 0))])

    def test_unapproved_leave_does_not_block(self):
        LeaveRequest.objects.create(
            staff_member=self.staff,
            leave_type='ANNUAL',
            start_datetime=_date_to_aware_datetime(date(2025, 3, 10), time(0, 0)),
            end_datetime=_date_to_aware_datetime(date(2025, 3, 10), time(23, 59)),
            status='REQUESTED',
        )
        result = get_staff_availability(self.staff.id, date(2025, 3, 10))
        self.assertEqual(len(result), 2)  # Still has both shifts

    def test_blocked_time_subtracts(self):
        BlockedTime.objects.create(
            staff_member=self.staff,
            start_datetime=_date_to_aware_datetime(date(2025, 3, 10), time(15, 0)),
            end_datetime=_date_to_aware_datetime(date(2025, 3, 10), time(16, 0)),
            reason='Meeting',
        )
        result = get_staff_availability(self.staff.id, date(2025, 3, 10))
        self.assertEqual(result, [
            (time(9, 0), time(12, 0)),
            (time(13, 0), time(15, 0)),
            (time(16, 0), time(17, 0)),
        ])

    def test_global_block_applies(self):
        BlockedTime.objects.create(
            staff_member=None,  # Global
            start_datetime=_date_to_aware_datetime(date(2025, 3, 10), time(9, 0)),
            end_datetime=_date_to_aware_datetime(date(2025, 3, 10), time(10, 0)),
            reason='Fire drill',
        )
        result = get_staff_availability(self.staff.id, date(2025, 3, 10))
        self.assertEqual(result[0], (time(10, 0), time(12, 0)))


class GetFreeSlotsTest(TestCase):
    def setUp(self):
        self.staff = Staff.objects.create(
            name='Slot Therapist', email='slots@example.com', phone='07000000001'
        )
        self.pattern = WorkingPattern.objects.create(
            staff_member=self.staff, name='Default', is_active=True
        )
        # Mon 9-12 only
        WorkingPatternRule.objects.create(
            working_pattern=self.pattern, weekday=0,
            start_time=time(9, 0), end_time=time(12, 0),
        )

    def test_generates_slots(self):
        # 2025-03-10 is Monday
        slots = get_free_slots(self.staff.id, date(2025, 3, 10), slot_minutes=60)
        # 9:00, 9:15, 9:30, 9:45, 10:00, 10:15, 10:30, 10:45, 11:00
        # (last slot that fits: 11:00-12:00)
        self.assertTrue(len(slots) > 0)
        self.assertEqual(slots[0]['start'][:16], '2025-03-10T09:00')

    def test_no_slots_on_weekend(self):
        slots = get_free_slots(self.staff.id, date(2025, 3, 9), slot_minutes=60)
        self.assertEqual(slots, [])

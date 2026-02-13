"""
Demo availability data seed / delete API endpoints.
POST   /api/demo/availability/seed/  — seed demo availability data
DELETE /api/demo/availability/seed/  — remove all demo availability data
GET    /api/demo/availability/seed/  — check if demo availability data exists
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models_availability import (
    WorkingPattern, WorkingPatternRule,
    AvailabilityOverride, AvailabilityOverridePeriod,
    LeaveRequest, BlockedTime, Shift, TimesheetEntry,
)
from .models import Booking

DEMO_TAG = 'avail-demo'


def _count_demo():
    """Count all demo availability records."""
    return {
        'patterns': WorkingPattern.objects.filter(name__contains=DEMO_TAG).count(),
        'rules': WorkingPatternRule.objects.filter(working_pattern__name__contains=DEMO_TAG).count(),
        'overrides': AvailabilityOverride.objects.filter(reason__contains=DEMO_TAG).count(),
        'leave_requests': LeaveRequest.objects.filter(reason__contains=DEMO_TAG).count(),
        'blocked_times': BlockedTime.objects.filter(reason__contains=DEMO_TAG).count(),
        'shifts': Shift.objects.filter(notes__contains=DEMO_TAG).count(),
        'timesheets': TimesheetEntry.objects.filter(notes__contains=DEMO_TAG).count(),
        'bookings': Booking.objects.filter(notes__contains=DEMO_TAG).count(),
    }


def _delete_demo():
    """Delete all demo availability data. Returns counts."""
    counts = {}
    counts['timesheets'] = TimesheetEntry.objects.filter(notes__contains=DEMO_TAG).delete()[0]
    counts['shifts'] = Shift.objects.filter(notes__contains=DEMO_TAG).delete()[0]
    counts['blocked_times'] = BlockedTime.objects.filter(reason__contains=DEMO_TAG).delete()[0]
    counts['leave_requests'] = LeaveRequest.objects.filter(reason__contains=DEMO_TAG).delete()[0]
    counts['override_periods'] = AvailabilityOverridePeriod.objects.filter(
        availability_override__reason__contains=DEMO_TAG
    ).delete()[0]
    counts['overrides'] = AvailabilityOverride.objects.filter(reason__contains=DEMO_TAG).delete()[0]
    counts['rules'] = WorkingPatternRule.objects.filter(
        working_pattern__name__contains=DEMO_TAG
    ).delete()[0]
    counts['patterns'] = WorkingPattern.objects.filter(name__contains=DEMO_TAG).delete()[0]
    counts['bookings'] = Booking.objects.filter(notes__contains=DEMO_TAG).delete()[0]
    return counts


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def demo_availability_seed_view(request):
    """
    GET    — check if demo availability data exists
    POST   — seed demo availability data
    DELETE — remove all demo availability data
    """
    if request.method == 'GET':
        counts = _count_demo()
        total = sum(counts.values())
        return Response({
            'has_demo': total > 0,
            'total': total,
            'counts': counts,
        })

    if request.method == 'DELETE':
        counts = _delete_demo()
        total = sum(counts.values())
        return Response({
            'deleted': True,
            'total_deleted': total,
            'counts': counts,
        })

    # POST — seed
    from django.core.management import call_command
    from io import StringIO

    # Check if already seeded
    if WorkingPattern.objects.filter(name__contains=DEMO_TAG).exists():
        counts = _count_demo()
        return Response({
            'has_demo': True,
            'already_existed': True,
            'total': sum(counts.values()),
            'counts': counts,
        })

    out = StringIO()
    call_command('seed_staff_availability_demo', stdout=out)
    counts = _count_demo()
    return Response({
        'has_demo': True,
        'already_existed': False,
        'total': sum(counts.values()),
        'counts': counts,
        'output': out.getvalue(),
    })

"""
Staff Availability Engine — API Views
DRF endpoints for working patterns, overrides, leave, blocks, shifts, timesheets.
Includes copy-pattern and duplicate-pattern utility endpoints.
"""
from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models_availability import (
    WorkingPattern, WorkingPatternRule,
    AvailabilityOverride, AvailabilityOverridePeriod,
    LeaveRequest, BlockedTime, Shift, TimesheetEntry,
)
from .serializers_availability import (
    WorkingPatternSerializer, WorkingPatternWriteSerializer,
    WorkingPatternRuleSerializer,
    AvailabilityOverrideSerializer, AvailabilityOverrideWriteSerializer,
    AvailabilityOverridePeriodSerializer,
    LeaveRequestSerializer,
    BlockedTimeSerializer,
    ShiftSerializer,
    TimesheetEntrySerializer,
)
from .availability import get_staff_availability, get_free_slots


# ─────────────────────────────────────────────────────────────────────
# WorkingPattern + Rules
# ─────────────────────────────────────────────────────────────────────

class WorkingPatternViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = WorkingPattern.objects.select_related('staff_member').prefetch_related('rules').all()
        staff_id = self.request.query_params.get('staff')
        if staff_id:
            qs = qs.filter(staff_member_id=staff_id)
        active_only = self.request.query_params.get('active')
        if active_only == '1':
            qs = qs.filter(is_active=True)
        return qs

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return WorkingPatternWriteSerializer
        return WorkingPatternSerializer

    @action(detail=True, methods=['post'], url_path='copy-to')
    def copy_to(self, request, pk=None):
        """POST /working-patterns/<id>/copy-to/ — Copy pattern + rules to another staff member."""
        source = self.get_object()
        target_staff_id = request.data.get('staff_member')
        if not target_staff_id:
            return Response({'error': 'staff_member is required'}, status=status.HTTP_400_BAD_REQUEST)

        new_name = request.data.get('name', f'Copy of {source.name}')
        new_pattern = WorkingPattern.objects.create(
            staff_member_id=target_staff_id,
            name=new_name,
            timezone=source.timezone,
            is_active=True,
        )
        for rule in source.rules.all():
            WorkingPatternRule.objects.create(
                working_pattern=new_pattern,
                weekday=rule.weekday,
                start_time=rule.start_time,
                end_time=rule.end_time,
                sort_order=rule.sort_order,
            )
        return Response(
            WorkingPatternSerializer(new_pattern).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='duplicate')
    def duplicate(self, request, pk=None):
        """POST /working-patterns/<id>/duplicate/ — Duplicate pattern with new name + effective_from."""
        source = self.get_object()
        new_name = request.data.get('name', f'{source.name} (copy)')
        effective_from = request.data.get('effective_from')

        new_pattern = WorkingPattern.objects.create(
            staff_member=source.staff_member,
            name=new_name,
            timezone=source.timezone,
            is_active=True,
            effective_from=effective_from,
        )
        for rule in source.rules.all():
            WorkingPatternRule.objects.create(
                working_pattern=new_pattern,
                weekday=rule.weekday,
                start_time=rule.start_time,
                end_time=rule.end_time,
                sort_order=rule.sort_order,
            )
        # Optionally deactivate the old one
        if request.data.get('deactivate_source', False):
            source.is_active = False
            source.save(update_fields=['is_active', 'updated_at'])

        return Response(
            WorkingPatternSerializer(new_pattern).data,
            status=status.HTTP_201_CREATED,
        )


class WorkingPatternRuleViewSet(viewsets.ModelViewSet):
    serializer_class = WorkingPatternRuleSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = WorkingPatternRule.objects.all()
        pattern_id = self.request.query_params.get('pattern')
        if pattern_id:
            qs = qs.filter(working_pattern_id=pattern_id)
        return qs


# ─────────────────────────────────────────────────────────────────────
# AvailabilityOverride + Periods
# ─────────────────────────────────────────────────────────────────────

class AvailabilityOverrideViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = AvailabilityOverride.objects.select_related('staff_member').prefetch_related('periods').all()
        staff_id = self.request.query_params.get('staff')
        if staff_id:
            qs = qs.filter(staff_member_id=staff_id)
        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(date__gte=date_from)
        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return qs

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return AvailabilityOverrideWriteSerializer
        return AvailabilityOverrideSerializer


# ─────────────────────────────────────────────────────────────────────
# LeaveRequest
# ─────────────────────────────────────────────────────────────────────

class LeaveRequestViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveRequestSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = LeaveRequest.objects.select_related('staff_member').all()
        staff_id = self.request.query_params.get('staff')
        if staff_id:
            qs = qs.filter(staff_member_id=staff_id)
        leave_status = self.request.query_params.get('status')
        if leave_status:
            qs = qs.filter(status=leave_status)
        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(end_datetime__date__gte=date_from)
        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(start_datetime__date__lte=date_to)
        return qs

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        leave = self.get_object()
        leave.status = 'APPROVED'
        leave.save(update_fields=['status', 'updated_at'])
        return Response(LeaveRequestSerializer(leave).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        leave = self.get_object()
        leave.status = 'REJECTED'
        leave.save(update_fields=['status', 'updated_at'])
        return Response(LeaveRequestSerializer(leave).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        leave = self.get_object()
        leave.status = 'CANCELLED'
        leave.save(update_fields=['status', 'updated_at'])
        return Response(LeaveRequestSerializer(leave).data)


# ─────────────────────────────────────────────────────────────────────
# BlockedTime
# ─────────────────────────────────────────────────────────────────────

class BlockedTimeViewSet(viewsets.ModelViewSet):
    serializer_class = BlockedTimeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = BlockedTime.objects.select_related('staff_member').all()
        staff_id = self.request.query_params.get('staff')
        if staff_id:
            qs = qs.filter(staff_member_id=staff_id)
        return qs


# ─────────────────────────────────────────────────────────────────────
# Shift
# ─────────────────────────────────────────────────────────────────────

class ShiftViewSet(viewsets.ModelViewSet):
    serializer_class = ShiftSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Shift.objects.select_related('staff_member').all()
        staff_id = self.request.query_params.get('staff')
        if staff_id:
            qs = qs.filter(staff_member_id=staff_id)
        published = self.request.query_params.get('published')
        if published == '1':
            qs = qs.filter(published=True)
        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(start_datetime__date__gte=date_from)
        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(start_datetime__date__lte=date_to)
        return qs


# ─────────────────────────────────────────────────────────────────────
# TimesheetEntry
# ─────────────────────────────────────────────────────────────────────

class TimesheetEntryViewSet(viewsets.ModelViewSet):
    serializer_class = TimesheetEntrySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = TimesheetEntry.objects.select_related('staff_member').all()
        staff_id = self.request.query_params.get('staff')
        if staff_id:
            qs = qs.filter(staff_member_id=staff_id)
        ts_status = self.request.query_params.get('status')
        if ts_status:
            qs = qs.filter(status=ts_status)
        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(date__gte=date_from)
        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return qs

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        entry = self.get_object()
        entry.status = 'SUBMITTED'
        entry.save(update_fields=['status', 'updated_at'])
        return Response(TimesheetEntrySerializer(entry).data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        entry = self.get_object()
        entry.status = 'APPROVED'
        entry.save(update_fields=['status', 'updated_at'])
        return Response(TimesheetEntrySerializer(entry).data)


# ─────────────────────────────────────────────────────────────────────
# Availability query endpoint
# ─────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def staff_availability_view(request):
    """
    GET /api/availability/?staff=<id>&date=<YYYY-MM-DD>
    Returns computed availability ranges for a staff member on a date.
    """
    staff_id = request.query_params.get('staff')
    date_str = request.query_params.get('date')
    if not staff_id or not date_str:
        return Response(
            {'error': 'staff and date query params are required'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        from datetime import date as dt_date
        parts = date_str.split('-')
        target_date = dt_date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        return Response({'error': 'Invalid date format, use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

    ranges = get_staff_availability(int(staff_id), target_date)
    return Response({
        'staff_id': int(staff_id),
        'date': date_str,
        'ranges': [
            {'start': r[0].strftime('%H:%M'), 'end': r[1].strftime('%H:%M')}
            for r in ranges
        ],
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def staff_free_slots_view(request):
    """
    GET /api/availability/slots/?staff=<id>&date=<YYYY-MM-DD>&duration=<minutes>
    Returns bookable time slots for a staff member on a date.
    """
    staff_id = request.query_params.get('staff')
    date_str = request.query_params.get('date')
    duration = int(request.query_params.get('duration', 60))
    if not staff_id or not date_str:
        return Response(
            {'error': 'staff and date query params are required'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        from datetime import date as dt_date
        parts = date_str.split('-')
        target_date = dt_date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        return Response({'error': 'Invalid date format, use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

    slots = get_free_slots(int(staff_id), target_date, slot_minutes=duration)
    return Response({
        'staff_id': int(staff_id),
        'date': date_str,
        'duration_minutes': duration,
        'slots': slots,
    })

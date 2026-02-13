from datetime import date, datetime, timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Staff, StaffSchedule
from .models_availability import TimesheetEntry
from .serializers_availability import TimesheetEntrySerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def timesheets_list(request):
    """GET /api/staff/timesheets/ — list timesheet entries with optional filters."""
    qs = TimesheetEntry.objects.select_related('staff_member').all()
    staff_id = request.query_params.get('staff_id')
    if staff_id:
        qs = qs.filter(staff_member_id=staff_id)
    date_from = request.query_params.get('date_from')
    if date_from:
        qs = qs.filter(date__gte=date_from)
    date_to = request.query_params.get('date_to')
    if date_to:
        qs = qs.filter(date__lte=date_to)
    ts_status = request.query_params.get('status')
    if ts_status:
        qs = qs.filter(status=ts_status)
    serializer = TimesheetEntrySerializer(qs, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def timesheets_update(request, pk):
    """PATCH /api/staff/timesheets/<pk>/update/ — update a timesheet entry."""
    try:
        entry = TimesheetEntry.objects.get(pk=pk)
    except TimesheetEntry.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    data = request.data
    d = entry.date

    if 'actual_start' in data and data['actual_start']:
        t = data['actual_start']
        entry.actual_start = timezone.make_aware(datetime.combine(d, datetime.strptime(t, '%H:%M').time()))
    if 'actual_end' in data and data['actual_end']:
        t = data['actual_end']
        entry.actual_end = timezone.make_aware(datetime.combine(d, datetime.strptime(t, '%H:%M').time()))
    if 'actual_break_minutes' in data:
        entry.break_minutes = int(data['actual_break_minutes'])
    if 'status' in data:
        entry.status = data['status']
    if 'notes' in data:
        entry.notes = data['notes']

    entry.save()
    return Response(TimesheetEntrySerializer(entry).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def timesheets_generate(request):
    """POST /api/staff/timesheets/generate/
    Body: { date_from, date_to, staff_id? }
    Creates timesheet entries from StaffSchedule working hours for the date range.
    Skips dates that already have a timesheet entry for that staff member.
    """
    date_from_str = request.data.get('date_from')
    date_to_str = request.data.get('date_to')
    staff_id = request.data.get('staff_id')

    if not date_from_str or not date_to_str:
        return Response({'error': 'date_from and date_to are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        d_from = date.fromisoformat(date_from_str)
        d_to = date.fromisoformat(date_to_str)
    except ValueError:
        return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)

    # Get all working hour schedules
    schedules_qs = StaffSchedule.objects.select_related('staff').filter(is_working=True)
    if staff_id:
        schedules_qs = schedules_qs.filter(staff_id=staff_id)

    # Build lookup: staff_id -> { day_of_week -> [schedule entries] }
    schedule_map = {}
    for sched in schedules_qs:
        sid = sched.staff_id
        if sid not in schedule_map:
            schedule_map[sid] = {}
        dow = sched.day_of_week
        if dow not in schedule_map[sid]:
            schedule_map[sid][dow] = []
        schedule_map[sid][dow].append(sched)

    # Get existing timesheet entries to avoid duplicates
    existing = set(
        TimesheetEntry.objects.filter(
            date__gte=d_from, date__lte=d_to
        ).values_list('staff_member_id', 'date')
    )

    created_count = 0
    current = d_from
    while current <= d_to:
        dow = current.weekday()  # Monday=0
        for sid, days in schedule_map.items():
            if dow in days:
                for sched in days[dow]:
                    if (sid, current) in existing:
                        continue
                    # Create timesheet entry
                    sched_start = timezone.make_aware(
                        datetime.combine(current, sched.start_time)
                    )
                    sched_end = timezone.make_aware(
                        datetime.combine(current, sched.end_time)
                    )
                    TimesheetEntry.objects.create(
                        staff_member_id=sid,
                        date=current,
                        scheduled_start=sched_start,
                        scheduled_end=sched_end,
                        break_minutes=sched.break_minutes,
                        status='DRAFT',
                        source='GENERATED_FROM_PATTERN',
                    )
                    created_count += 1
                    existing.add((sid, current))
        current += timedelta(days=1)

    return Response({'detail': f'{created_count} timesheet entries generated.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def timesheets_summary(request):
    """GET /api/staff/timesheets/summary/ — summary stats for timesheets."""
    qs = TimesheetEntry.objects.select_related('staff_member').all()
    staff_id = request.query_params.get('staff_id')
    if staff_id:
        qs = qs.filter(staff_member_id=staff_id)
    period = request.query_params.get('period', 'week')
    ref_date = request.query_params.get('date')
    if ref_date:
        try:
            ref = date.fromisoformat(ref_date)
        except ValueError:
            ref = date.today()
    else:
        ref = date.today()

    if period == 'week':
        start = ref - timedelta(days=ref.weekday())
        end = start + timedelta(days=6)
    elif period == 'month':
        start = ref.replace(day=1)
        next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        end = next_month - timedelta(days=1)
    else:
        start = ref
        end = ref

    entries = qs.filter(date__gte=start, date__lte=end)
    total_scheduled = 0
    total_actual = 0
    for e in entries:
        sh = e.scheduled_hours
        ah = e.actual_hours
        if sh:
            total_scheduled += sh
        if ah:
            total_actual += ah

    return Response({
        'period': period,
        'start': start.isoformat(),
        'end': end.isoformat(),
        'total_entries': entries.count(),
        'total_scheduled_hours': round(total_scheduled, 2),
        'total_actual_hours': round(total_actual, 2),
        'variance': round(total_actual - total_scheduled, 2),
    })

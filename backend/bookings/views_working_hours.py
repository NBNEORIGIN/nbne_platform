from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import StaffSchedule
from .serializers_schedule import StaffScheduleSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def working_hours_list(request):
    """GET /api/staff/working-hours/ — list working hours, optionally filtered by staff_id."""
    qs = StaffSchedule.objects.select_related('staff').all()
    staff_id = request.query_params.get('staff_id')
    if staff_id:
        qs = qs.filter(staff_id=staff_id)
    serializer = StaffScheduleSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def working_hours_bulk_set(request):
    """POST /api/staff/working-hours/bulk-set/
    Body: { staff: <id>, hours: [{ day_of_week, start_time, end_time, break_minutes }] }
    Replaces all working hours for the given staff member.
    """
    staff_id = request.data.get('staff')
    hours = request.data.get('hours', [])

    if not staff_id:
        return Response({'error': 'staff is required'}, status=status.HTTP_400_BAD_REQUEST)

    # Delete existing entries for this staff
    StaffSchedule.objects.filter(staff_id=staff_id).delete()

    created = []
    for h in hours:
        obj = StaffSchedule.objects.create(
            staff_id=staff_id,
            day_of_week=h.get('day_of_week', 0),
            is_working=True,
            start_time=h.get('start_time', '09:00'),
            end_time=h.get('end_time', '17:00'),
            break_minutes=h.get('break_minutes', 0),
        )
        created.append(obj)

    serializer = StaffScheduleSerializer(created, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def working_hours_delete(request, pk):
    """DELETE /api/staff/working-hours/<pk>/delete/"""
    try:
        obj = StaffSchedule.objects.get(pk=pk)
    except StaffSchedule.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    obj.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

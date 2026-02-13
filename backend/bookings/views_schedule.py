from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import BusinessHours, StaffSchedule, Closure, StaffLeave
from .serializers_schedule import (
    BusinessHoursSerializer, 
    StaffScheduleSerializer, 
    ClosureSerializer, 
    StaffLeaveSerializer
)


class BusinessHoursViewSet(viewsets.ModelViewSet):
    queryset = BusinessHours.objects.all()
    serializer_class = BusinessHoursSerializer
    permission_classes = [AllowAny]


class StaffScheduleViewSet(viewsets.ModelViewSet):
    queryset = StaffSchedule.objects.all()
    serializer_class = StaffScheduleSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        staff_id = self.request.query_params.get('staff', None)
        if staff_id:
            queryset = queryset.filter(staff_id=staff_id)
        return queryset


class ClosureViewSet(viewsets.ModelViewSet):
    queryset = Closure.objects.all()
    serializer_class = ClosureSerializer
    permission_classes = [AllowAny]


class StaffLeaveViewSet(viewsets.ModelViewSet):
    queryset = StaffLeave.objects.all()
    serializer_class = StaffLeaveSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        staff_id = self.request.query_params.get('staff', None)
        if staff_id:
            queryset = queryset.filter(staff_id=staff_id)
        return queryset

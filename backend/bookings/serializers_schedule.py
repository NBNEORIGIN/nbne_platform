from rest_framework import serializers
from .models import BusinessHours, StaffSchedule, Closure, StaffLeave


class BusinessHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessHours
        fields = ['id', 'day_of_week', 'is_open', 'open_time', 'close_time']


class StaffScheduleSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    
    class Meta:
        model = StaffSchedule
        fields = ['id', 'staff', 'staff_name', 'day_of_week', 'is_working', 'start_time', 'end_time', 'break_minutes']


class ClosureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Closure
        fields = ['id', 'date', 'reason', 'all_day', 'start_time', 'end_time']


class StaffLeaveSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    
    class Meta:
        model = StaffLeave
        fields = ['id', 'staff', 'staff_name', 'start_date', 'end_date', 'reason']

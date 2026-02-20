from rest_framework import serializers
from .models_gym import ClassType, ClassSession


class ClassTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassType
        fields = [
            'id', 'name', 'description', 'category',
            'duration_minutes', 'difficulty', 'max_capacity',
            'colour', 'price_pence', 'active', 'sort_order',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ClassSessionSerializer(serializers.ModelSerializer):
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    class_type_name = serializers.CharField(source='class_type.name', read_only=True)
    instructor_name = serializers.CharField(source='instructor.name', read_only=True, default=None)
    capacity = serializers.IntegerField(read_only=True)

    class Meta:
        model = ClassSession
        fields = [
            'id', 'class_type', 'class_type_name',
            'instructor', 'instructor_name',
            'day_of_week', 'day_of_week_display',
            'start_time', 'end_time', 'room',
            'override_capacity', 'capacity',
            'active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

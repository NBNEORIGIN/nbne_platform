"""
Staff Availability Engine — Serializers
"""
from rest_framework import serializers
from .models_availability import (
    WorkingPattern, WorkingPatternRule,
    AvailabilityOverride, AvailabilityOverridePeriod,
    LeaveRequest, BlockedTime, Shift, TimesheetEntry,
)


# ─────────────────────────────────────────────────────────────────────
# WorkingPattern + Rules
# ─────────────────────────────────────────────────────────────────────

class WorkingPatternRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkingPatternRule
        fields = ['id', 'weekday', 'start_time', 'end_time', 'sort_order']


class WorkingPatternSerializer(serializers.ModelSerializer):
    rules = WorkingPatternRuleSerializer(many=True, read_only=True)
    staff_name = serializers.CharField(source='staff_member.name', read_only=True)

    class Meta:
        model = WorkingPattern
        fields = [
            'id', 'staff_member', 'staff_name', 'name', 'timezone',
            'is_active', 'effective_from', 'effective_to',
            'rules', 'created_at', 'updated_at',
        ]


class WorkingPatternWriteSerializer(serializers.ModelSerializer):
    """Write serializer that accepts nested rules inline."""
    rules = WorkingPatternRuleSerializer(many=True, required=False)

    class Meta:
        model = WorkingPattern
        fields = [
            'id', 'staff_member', 'name', 'timezone',
            'is_active', 'effective_from', 'effective_to', 'rules',
        ]

    def create(self, validated_data):
        rules_data = validated_data.pop('rules', [])
        pattern = WorkingPattern.objects.create(**validated_data)
        for rule_data in rules_data:
            WorkingPatternRule.objects.create(working_pattern=pattern, **rule_data)
        return pattern

    def update(self, instance, validated_data):
        rules_data = validated_data.pop('rules', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if rules_data is not None:
            instance.rules.all().delete()
            for rule_data in rules_data:
                WorkingPatternRule.objects.create(working_pattern=instance, **rule_data)
        return instance


# ─────────────────────────────────────────────────────────────────────
# AvailabilityOverride + Periods
# ─────────────────────────────────────────────────────────────────────

class AvailabilityOverridePeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilityOverridePeriod
        fields = ['id', 'start_time', 'end_time', 'sort_order']


class AvailabilityOverrideSerializer(serializers.ModelSerializer):
    periods = AvailabilityOverridePeriodSerializer(many=True, read_only=True)
    staff_name = serializers.CharField(source='staff_member.name', read_only=True)

    class Meta:
        model = AvailabilityOverride
        fields = [
            'id', 'staff_member', 'staff_name', 'date', 'mode',
            'reason', 'created_by', 'periods', 'created_at', 'updated_at',
        ]


class AvailabilityOverrideWriteSerializer(serializers.ModelSerializer):
    """Write serializer that accepts nested periods inline."""
    periods = AvailabilityOverridePeriodSerializer(many=True, required=False)

    class Meta:
        model = AvailabilityOverride
        fields = [
            'id', 'staff_member', 'date', 'mode', 'reason', 'created_by', 'periods',
        ]

    def validate(self, data):
        mode = data.get('mode', getattr(self.instance, 'mode', None))
        periods = data.get('periods', [])
        if mode == 'CLOSED' and periods:
            raise serializers.ValidationError('CLOSED overrides must not have periods')
        if mode in ('REPLACE', 'ADD', 'REMOVE') and not periods:
            if not self.instance:
                raise serializers.ValidationError(f'{mode} overrides should have at least one period')
        return data

    def create(self, validated_data):
        periods_data = validated_data.pop('periods', [])
        override = AvailabilityOverride.objects.create(**validated_data)
        for period_data in periods_data:
            AvailabilityOverridePeriod.objects.create(
                availability_override=override, **period_data
            )
        return override

    def update(self, instance, validated_data):
        periods_data = validated_data.pop('periods', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if periods_data is not None:
            instance.periods.all().delete()
            for period_data in periods_data:
                AvailabilityOverridePeriod.objects.create(
                    availability_override=instance, **period_data
                )
        return instance


# ─────────────────────────────────────────────────────────────────────
# LeaveRequest
# ─────────────────────────────────────────────────────────────────────

class LeaveRequestSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff_member.name', read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'staff_member', 'staff_name', 'leave_type',
            'start_datetime', 'end_datetime', 'status', 'reason',
            'created_by', 'approved_by', 'created_at', 'updated_at',
        ]


# ─────────────────────────────────────────────────────────────────────
# BlockedTime
# ─────────────────────────────────────────────────────────────────────

class BlockedTimeSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff_member.name', read_only=True, default='ALL STAFF')

    class Meta:
        model = BlockedTime
        fields = [
            'id', 'staff_member', 'staff_name', 'start_datetime', 'end_datetime',
            'reason', 'created_by', 'created_at', 'updated_at',
        ]


# ─────────────────────────────────────────────────────────────────────
# Shift
# ─────────────────────────────────────────────────────────────────────

class ShiftSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff_member.name', read_only=True)

    class Meta:
        model = Shift
        fields = [
            'id', 'staff_member', 'staff_name', 'start_datetime', 'end_datetime',
            'location', 'published', 'notes', 'created_at', 'updated_at',
        ]


# ─────────────────────────────────────────────────────────────────────
# TimesheetEntry
# ─────────────────────────────────────────────────────────────────────

class TimesheetEntrySerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff_member.name', read_only=True)
    scheduled_hours = serializers.FloatField(read_only=True)
    actual_hours = serializers.FloatField(read_only=True)
    variance = serializers.FloatField(read_only=True)

    class Meta:
        model = TimesheetEntry
        fields = [
            'id', 'staff_member', 'staff_name', 'date',
            'scheduled_start', 'scheduled_end', 'actual_start', 'actual_end',
            'break_minutes', 'status', 'source', 'notes',
            'scheduled_hours', 'actual_hours', 'variance',
            'created_at', 'updated_at',
        ]

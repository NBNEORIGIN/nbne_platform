"""
Migration: Staff Availability Engine
Creates: WorkingPattern, WorkingPatternRule, AvailabilityOverride,
         AvailabilityOverridePeriod, LeaveRequest, BlockedTime, Shift, TimesheetEntry
"""
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bookings', '0010_service_intelligence_layer'),
    ]

    operations = [
        # A) WorkingPattern
        migrations.CreateModel(
            name='WorkingPattern',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Default', max_length=120)),
                ('timezone', models.CharField(default='Europe/London', max_length=50)),
                ('is_active', models.BooleanField(default=True)),
                ('effective_from', models.DateField(blank=True, null=True)),
                ('effective_to', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('staff_member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='working_patterns', to='bookings.staff')),
            ],
            options={
                'ordering': ['-is_active', '-created_at'],
            },
        ),
        # B) WorkingPatternRule
        migrations.CreateModel(
            name='WorkingPatternRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekday', models.IntegerField(choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')])),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('sort_order', models.IntegerField(default=0)),
                ('working_pattern', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rules', to='bookings.workingpattern')),
            ],
            options={
                'ordering': ['weekday', 'sort_order', 'start_time'],
            },
        ),
        # C) AvailabilityOverride
        migrations.CreateModel(
            name='AvailabilityOverride',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('mode', models.CharField(choices=[('REPLACE', 'Replace (override full day)'), ('ADD', 'Add (union with weekly)'), ('REMOVE', 'Remove (subtract from weekly)'), ('CLOSED', 'Closed (no work that day)')], max_length=10)),
                ('reason', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('staff_member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='availability_overrides', to='bookings.staff')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_overrides', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['date'],
                'unique_together': {('staff_member', 'date')},
            },
        ),
        # D) AvailabilityOverridePeriod
        migrations.CreateModel(
            name='AvailabilityOverridePeriod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('sort_order', models.IntegerField(default=0)),
                ('availability_override', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='periods', to='bookings.availabilityoverride')),
            ],
            options={
                'ordering': ['sort_order', 'start_time'],
            },
        ),
        # E) LeaveRequest
        migrations.CreateModel(
            name='LeaveRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('leave_type', models.CharField(choices=[('ANNUAL', 'Annual Leave'), ('SICK', 'Sick Leave'), ('UNPAID', 'Unpaid Leave'), ('OTHER', 'Other')], max_length=10)),
                ('start_datetime', models.DateTimeField()),
                ('end_datetime', models.DateTimeField()),
                ('status', models.CharField(choices=[('REQUESTED', 'Requested'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('CANCELLED', 'Cancelled')], default='REQUESTED', max_length=10)),
                ('reason', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('staff_member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leave_requests', to='bookings.staff')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_leave_requests', to=settings.AUTH_USER_MODEL)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_leave_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-start_datetime'],
            },
        ),
        # F) BlockedTime
        migrations.CreateModel(
            name='BlockedTime',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_datetime', models.DateTimeField()),
                ('end_datetime', models.DateTimeField()),
                ('reason', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('staff_member', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='blocked_times', to='bookings.staff', help_text='Null = applies to ALL staff')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_blocked_times', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['start_datetime'],
            },
        ),
        # G) Shift
        migrations.CreateModel(
            name='Shift',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_datetime', models.DateTimeField()),
                ('end_datetime', models.DateTimeField()),
                ('location', models.CharField(blank=True, default='', max_length=200)),
                ('published', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('staff_member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shifts', to='bookings.staff')),
            ],
            options={
                'ordering': ['start_datetime'],
            },
        ),
        # H) TimesheetEntry
        migrations.CreateModel(
            name='TimesheetEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('scheduled_start', models.DateTimeField(blank=True, null=True)),
                ('scheduled_end', models.DateTimeField(blank=True, null=True)),
                ('actual_start', models.DateTimeField(blank=True, null=True)),
                ('actual_end', models.DateTimeField(blank=True, null=True)),
                ('break_minutes', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('SUBMITTED', 'Submitted'), ('APPROVED', 'Approved')], default='DRAFT', max_length=10)),
                ('source', models.CharField(choices=[('MANUAL', 'Manual Entry'), ('CLOCK_IN_OUT', 'Clock In/Out'), ('GENERATED_FROM_SHIFT', 'Generated from Shift'), ('GENERATED_FROM_PATTERN', 'Generated from Pattern')], default='MANUAL', max_length=30)),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('staff_member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='timesheet_entries', to='bookings.staff')),
            ],
            options={
                'ordering': ['-date'],
                'unique_together': {('staff_member', 'date')},
            },
        ),
    ]

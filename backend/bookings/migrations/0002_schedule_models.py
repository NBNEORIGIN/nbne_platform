# Generated migration for schedule models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessHours',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day_of_week', models.IntegerField(choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')], unique=True)),
                ('is_open', models.BooleanField(default=True)),
                ('open_time', models.TimeField(default='09:00')),
                ('close_time', models.TimeField(default='17:00')),
            ],
            options={
                'verbose_name_plural': 'Business Hours',
                'ordering': ['day_of_week'],
            },
        ),
        migrations.CreateModel(
            name='Closure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(unique=True)),
                ('reason', models.CharField(max_length=200)),
                ('all_day', models.BooleanField(default=True)),
                ('start_time', models.TimeField(blank=True, null=True)),
                ('end_time', models.TimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['date'],
            },
        ),
        migrations.CreateModel(
            name='StaffLeave',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('reason', models.CharField(blank=True, max_length=200)),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leave', to='bookings.staff')),
            ],
            options={
                'verbose_name': 'Staff Leave',
                'verbose_name_plural': 'Staff Leave',
                'ordering': ['start_date'],
            },
        ),
        migrations.CreateModel(
            name='StaffSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day_of_week', models.IntegerField(choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')])),
                ('is_working', models.BooleanField(default=True)),
                ('start_time', models.TimeField(default='09:00')),
                ('end_time', models.TimeField(default='17:00')),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedules', to='bookings.staff')),
            ],
            options={
                'verbose_name': 'Staff Schedule',
                'ordering': ['staff', 'day_of_week'],
                'unique_together': {('staff', 'day_of_week')},
            },
        ),
    ]

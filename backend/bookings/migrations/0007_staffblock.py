from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0006_enhance_service_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='StaffBlock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('reason', models.CharField(blank=True, max_length=200)),
                ('all_day', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocks', to='bookings.staff')),
            ],
            options={
                'verbose_name': 'Staff Block',
                'ordering': ['date', 'start_time'],
            },
        ),
    ]

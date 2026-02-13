from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0011_availability_engine'),
    ]

    operations = [
        # Service
        migrations.AddField(
            model_name='service',
            name='data_origin',
            field=models.CharField(choices=[('REAL', 'Real'), ('DEMO', 'Demo')], db_index=True, default='REAL', max_length=4),
        ),
        migrations.AddField(
            model_name='service',
            name='demo_seed_id',
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        # Client
        migrations.AddField(
            model_name='client',
            name='data_origin',
            field=models.CharField(choices=[('REAL', 'Real'), ('DEMO', 'Demo')], db_index=True, default='REAL', max_length=4),
        ),
        migrations.AddField(
            model_name='client',
            name='demo_seed_id',
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        # Booking
        migrations.AddField(
            model_name='booking',
            name='data_origin',
            field=models.CharField(choices=[('REAL', 'Real'), ('DEMO', 'Demo')], db_index=True, default='REAL', max_length=4),
        ),
        migrations.AddField(
            model_name='booking',
            name='demo_seed_id',
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
    ]

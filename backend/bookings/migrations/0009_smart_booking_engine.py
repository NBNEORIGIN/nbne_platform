from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0008_staff_role'),
    ]

    operations = [
        # Client — reliability tracking
        migrations.AddField(model_name='client', name='total_bookings', field=models.IntegerField(default=0)),
        migrations.AddField(model_name='client', name='completed_bookings', field=models.IntegerField(default=0)),
        migrations.AddField(model_name='client', name='cancelled_bookings', field=models.IntegerField(default=0)),
        migrations.AddField(model_name='client', name='no_show_count', field=models.IntegerField(default=0)),
        migrations.AddField(model_name='client', name='consecutive_no_shows', field=models.IntegerField(default=0)),
        migrations.AddField(model_name='client', name='last_no_show_date', field=models.DateTimeField(null=True, blank=True)),
        migrations.AddField(model_name='client', name='reliability_score', field=models.FloatField(default=100.0)),
        migrations.AddField(model_name='client', name='lifetime_value', field=models.DecimalField(max_digits=10, decimal_places=2, default=0)),
        migrations.AddField(model_name='client', name='avg_days_between_bookings', field=models.FloatField(null=True, blank=True)),

        # Booking — risk & recommendation
        migrations.AddField(model_name='booking', name='risk_score', field=models.FloatField(null=True, blank=True)),
        migrations.AddField(model_name='booking', name='risk_level', field=models.CharField(max_length=10, blank=True, default='')),
        migrations.AddField(model_name='booking', name='revenue_at_risk', field=models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)),
        migrations.AddField(model_name='booking', name='recommended_payment_type', field=models.CharField(max_length=30, blank=True, default='')),
        migrations.AddField(model_name='booking', name='recommended_deposit_percent', field=models.FloatField(null=True, blank=True)),
        migrations.AddField(model_name='booking', name='recommended_price_adjustment', field=models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)),
        migrations.AddField(model_name='booking', name='recommended_incentive', field=models.CharField(max_length=200, blank=True, default='')),
        migrations.AddField(model_name='booking', name='recommendation_reason', field=models.TextField(blank=True, default='')),
        migrations.AddField(model_name='booking', name='optimisation_snapshot', field=models.JSONField(null=True, blank=True)),
        migrations.AddField(model_name='booking', name='override_applied', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='booking', name='override_reason', field=models.TextField(blank=True, default='')),

        # Service — demand intelligence
        migrations.AddField(model_name='service', name='demand_index', field=models.FloatField(default=0, help_text='Normalised 0-100 demand score')),
        migrations.AddField(model_name='service', name='peak_time_multiplier', field=models.FloatField(default=1.0)),
        migrations.AddField(model_name='service', name='off_peak_discount_allowed', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='service', name='no_show_adjustment_enabled', field=models.BooleanField(default=True)),

        # OptimisationLog — R&D evidence (Phase 6+8)
        migrations.CreateModel(
            name='OptimisationLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('booking', models.ForeignKey(on_delete=models.CASCADE, related_name='optimisation_logs', to='bookings.booking', null=True, blank=True)),
                ('input_data', models.JSONField(null=True, blank=True)),
                ('output_recommendation', models.JSONField(null=True, blank=True)),
                ('override_applied', models.BooleanField(default=False)),
                ('override_reason', models.TextField(blank=True, default='')),
                ('reliability_score', models.FloatField(null=True, blank=True)),
                ('risk_score', models.FloatField(null=True, blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-timestamp'],
                'verbose_name': 'Optimisation Log',
            },
        ),
    ]

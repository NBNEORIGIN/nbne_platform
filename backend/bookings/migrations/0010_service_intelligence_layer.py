"""Service Intelligence Layer — new fields for adaptive pricing & optimisation."""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0009_smart_booking_engine'),
    ]

    operations = [
        # Service intelligence fields
        migrations.AddField(
            model_name='service',
            name='avg_booking_value',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='service',
            name='total_revenue',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='service',
            name='total_bookings',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='service',
            name='no_show_rate',
            field=models.FloatField(default=0, help_text='Percentage 0-100'),
        ),
        migrations.AddField(
            model_name='service',
            name='avg_risk_score',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='service',
            name='peak_utilisation_rate',
            field=models.FloatField(default=0, help_text='Percentage 0-100'),
        ),
        migrations.AddField(
            model_name='service',
            name='off_peak_utilisation_rate',
            field=models.FloatField(default=0, help_text='Percentage 0-100'),
        ),
        migrations.AddField(
            model_name='service',
            name='recommended_base_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='service',
            name='recommended_deposit_percent',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='service',
            name='recommended_payment_type',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
        migrations.AddField(
            model_name='service',
            name='price_elasticity_index',
            field=models.FloatField(default=0, help_text='0-100 sensitivity score'),
        ),
        migrations.AddField(
            model_name='service',
            name='recommendation_reason',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='service',
            name='recommendation_confidence',
            field=models.FloatField(default=0, help_text='0-100 confidence'),
        ),
        migrations.AddField(
            model_name='service',
            name='recommendation_snapshot',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='service',
            name='last_optimised_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='service',
            name='auto_optimise_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='service',
            name='deposit_strategy',
            field=models.CharField(choices=[('fixed', 'Fixed'), ('percentage', 'Percentage'), ('dynamic', 'Dynamic (AI Assisted)')], default='fixed', max_length=20),
        ),
        migrations.AddField(
            model_name='service',
            name='smart_pricing_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='service',
            name='off_peak_discount_percent',
            field=models.FloatField(default=0),
        ),
        # ServiceOptimisationLog model
        migrations.CreateModel(
            name='ServiceOptimisationLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('previous_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('new_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('previous_deposit', models.IntegerField(blank=True, null=True)),
                ('new_deposit', models.IntegerField(blank=True, null=True)),
                ('reason', models.TextField(blank=True, default='')),
                ('ai_recommended', models.BooleanField(default=False)),
                ('owner_override', models.BooleanField(default=False)),
                ('input_metrics', models.JSONField(blank=True, null=True)),
                ('output_recommendation', models.JSONField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='optimisation_logs', to='bookings.service')),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
    ]

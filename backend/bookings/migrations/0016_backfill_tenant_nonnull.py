"""Backfill NULL tenant FKs on Service, Staff, Client, Booking, then make non-nullable."""
import django.db.models.deletion
from django.db import migrations, models


def backfill(apps, schema_editor):
    TenantSettings = apps.get_model('tenants', 'TenantSettings')
    default = TenantSettings.objects.first()
    if not default:
        return
    for model_name in ('Service', 'Staff', 'Client', 'Booking'):
        Model = apps.get_model('bookings', model_name)
        Model.objects.filter(tenant__isnull=True).update(tenant=default)


class Migration(migrations.Migration):
    dependencies = [
        ('bookings', '0015_booking_tenant_client_tenant_service_tenant_and_more'),
        ('tenants', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='service',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='services', to='tenants.tenantsettings'),
        ),
        migrations.AlterField(
            model_name='staff',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='booking_staff', to='tenants.tenantsettings'),
        ),
        migrations.AlterField(
            model_name='client',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='clients', to='tenants.tenantsettings'),
        ),
        migrations.AlterField(
            model_name='booking',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='tenants.tenantsettings'),
        ),
    ]

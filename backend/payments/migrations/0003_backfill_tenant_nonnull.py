"""Backfill NULL tenant FKs on Customer and PaymentSession, then make non-nullable."""
import django.db.models.deletion
from django.db import migrations, models


def backfill(apps, schema_editor):
    TenantSettings = apps.get_model('tenants', 'TenantSettings')
    default = TenantSettings.objects.first()
    if not default:
        return
    # Only Customer has a tenant FK (added in 0002). PaymentSession does not.
    Customer = apps.get_model('payments', 'Customer')
    Customer.objects.filter(tenant__isnull=True).update(tenant=default)


class Migration(migrations.Migration):
    dependencies = [
        ('payments', '0002_customer_tenant_alter_customer_email'),
        ('tenants', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='customer',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_customers', to='tenants.tenantsettings'),
        ),
    ]

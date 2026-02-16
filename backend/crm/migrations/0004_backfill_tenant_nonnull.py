"""Backfill NULL tenant FKs on Lead, then make non-nullable."""
import django.db.models.deletion
from django.db import migrations, models


def backfill(apps, schema_editor):
    TenantSettings = apps.get_model('tenants', 'TenantSettings')
    default = TenantSettings.objects.first()
    if not default:
        return
    Lead = apps.get_model('crm', 'Lead')
    Lead.objects.filter(tenant__isnull=True).update(tenant=default)


class Migration(migrations.Migration):
    dependencies = [
        ('crm', '0003_lead_tenant'),
        ('tenants', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='lead',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leads', to='tenants.tenantsettings'),
        ),
    ]

"""Backfill NULL tenant FKs on BusinessEvent, then make non-nullable."""
import django.db.models.deletion
from django.db import migrations, models


def backfill(apps, schema_editor):
    TenantSettings = apps.get_model('tenants', 'TenantSettings')
    default = TenantSettings.objects.first()
    if not default:
        return
    BusinessEvent = apps.get_model('core', 'BusinessEvent')
    BusinessEvent.objects.filter(tenant__isnull=True).update(tenant=default)


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0004_businessevent_tenant'),
        ('tenants', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='businessevent',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='business_events', to='tenants.tenantsettings'),
        ),
    ]

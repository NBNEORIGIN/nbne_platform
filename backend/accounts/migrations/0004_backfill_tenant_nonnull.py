"""Backfill NULL tenant FKs on User. User.tenant stays nullable (SET_NULL)."""
from django.db import migrations


def backfill(apps, schema_editor):
    TenantSettings = apps.get_model('tenants', 'TenantSettings')
    default = TenantSettings.objects.first()
    if not default:
        return
    User = apps.get_model('accounts', 'User')
    User.objects.filter(tenant__isnull=True).update(tenant=default)


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0003_user_tenant'),
        ('tenants', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]

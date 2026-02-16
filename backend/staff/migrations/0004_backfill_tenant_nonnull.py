"""Backfill NULL tenant FKs on StaffProfile, then make non-nullable."""
import django.db.models.deletion
from django.db import migrations, models


def backfill(apps, schema_editor):
    TenantSettings = apps.get_model('tenants', 'TenantSettings')
    default = TenantSettings.objects.first()
    if not default:
        return
    StaffProfile = apps.get_model('staff', 'StaffProfile')
    StaffProfile.objects.filter(tenant__isnull=True).update(tenant=default)


class Migration(migrations.Migration):
    dependencies = [
        ('staff', '0003_rename_staff_timesh_staff_i_idx_staff_times_staff_i_23ef5f_idx_and_more'),
        ('tenants', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='staffprofile',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='staff_profiles', to='tenants.tenantsettings'),
        ),
    ]

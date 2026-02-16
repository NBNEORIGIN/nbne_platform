"""Backfill NULL tenant FKs on Document and DocumentTag, then make non-nullable."""
import django.db.models.deletion
from django.db import migrations, models


def backfill(apps, schema_editor):
    TenantSettings = apps.get_model('tenants', 'TenantSettings')
    default = TenantSettings.objects.first()
    if not default:
        return
    for model_name in ('Document', 'DocumentTag'):
        Model = apps.get_model('documents', model_name)
        Model.objects.filter(tenant__isnull=True).update(tenant=default)


class Migration(migrations.Migration):
    dependencies = [
        ('documents', '0003_document_tenant_documenttag_tenant_and_more'),
        ('tenants', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='document',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='tenants.tenantsettings'),
        ),
        migrations.AlterField(
            model_name='documenttag',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='document_tags', to='tenants.tenantsettings'),
        ),
    ]

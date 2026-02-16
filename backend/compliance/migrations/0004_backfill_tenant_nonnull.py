"""Backfill NULL tenant FKs on all compliance models, then make non-nullable."""
import django.db.models.deletion
from django.db import migrations, models


def backfill(apps, schema_editor):
    TenantSettings = apps.get_model('tenants', 'TenantSettings')
    default = TenantSettings.objects.first()
    if not default:
        return
    for model_name in ('IncidentReport', 'RiskAssessment', 'Equipment',
                        'ComplianceCategory', 'AccidentReport', 'PeaceOfMindScore',
                        'RAMSDocument'):
        Model = apps.get_model('compliance', model_name)
        Model.objects.filter(tenant__isnull=True).update(tenant=default)


class Migration(migrations.Migration):
    dependencies = [
        ('compliance', '0003_accidentreport_tenant_compliancecategory_tenant_and_more'),
        ('tenants', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='incidentreport',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incidents', to='tenants.tenantsettings'),
        ),
        migrations.AlterField(
            model_name='riskassessment',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='risk_assessments', to='tenants.tenantsettings'),
        ),
        migrations.AlterField(
            model_name='equipment',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='equipment', to='tenants.tenantsettings'),
        ),
        migrations.AlterField(
            model_name='compliancecategory',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='compliance_categories', to='tenants.tenantsettings'),
        ),
        migrations.AlterField(
            model_name='accidentreport',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accident_reports', to='tenants.tenantsettings'),
        ),
        migrations.AlterField(
            model_name='peaceofmindscore',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='peace_of_mind_scores', to='tenants.tenantsettings'),
        ),
        migrations.AlterField(
            model_name='ramsdocument',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rams_documents', to='tenants.tenantsettings'),
        ),
    ]

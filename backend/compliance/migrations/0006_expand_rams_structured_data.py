"""Expand RAMSDocument with structured JSON fields for the RAMS generator."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compliance', '0005_wiggum_fields'),
    ]

    operations = [
        # Make document field optional (was required, now RAMS can be structured-only)
        migrations.AlterField(
            model_name='ramsdocument',
            name='document',
            field=models.FileField(blank=True, null=True, upload_to='compliance/rams/%Y/%m/'),
        ),
        # Applicable sections — controls which sections are checked for completeness
        migrations.AddField(
            model_name='ramsdocument',
            name='applicable_sections',
            field=models.JSONField(blank=True, default=list, help_text='List of section keys that apply to this RAMS. Sections not listed are N/A.'),
        ),
        # Structured section data
        migrations.AddField(
            model_name='ramsdocument',
            name='job_details',
            field=models.JSONField(blank=True, null=True, help_text='Client name, site address, job description, dates, scope of work'),
        ),
        migrations.AddField(
            model_name='ramsdocument',
            name='personnel',
            field=models.JSONField(blank=True, null=True, help_text='List of personnel: [{name, role, qualifications, responsibilities}]'),
        ),
        migrations.AddField(
            model_name='ramsdocument',
            name='equipment',
            field=models.JSONField(blank=True, null=True, help_text='List of equipment: [{name, inspection_date, cert_ref, notes}]'),
        ),
        migrations.AddField(
            model_name='ramsdocument',
            name='hazards',
            field=models.JSONField(blank=True, null=True, help_text='List of hazards: [{description, controls, initial_likelihood, initial_severity, residual_likelihood, residual_severity}]'),
        ),
        migrations.AddField(
            model_name='ramsdocument',
            name='method_statement',
            field=models.JSONField(blank=True, null=True, help_text='Ordered steps: [{step_number, description, responsible, hazard_refs}]'),
        ),
        migrations.AddField(
            model_name='ramsdocument',
            name='emergency_procedures',
            field=models.JSONField(blank=True, null=True, help_text='Emergency contacts, first aiders, evacuation procedures, nearest hospital'),
        ),
        migrations.AddField(
            model_name='ramsdocument',
            name='environmental',
            field=models.JSONField(blank=True, null=True, help_text='Environmental considerations: waste disposal, noise, protected areas'),
        ),
        migrations.AddField(
            model_name='ramsdocument',
            name='permits',
            field=models.JSONField(blank=True, null=True, help_text='Required permits: [{type, reference, issued_by, expiry}]'),
        ),
        migrations.AddField(
            model_name='ramsdocument',
            name='monitoring',
            field=models.JSONField(blank=True, null=True, help_text='Review schedule, sign-off requirements, toolbox talk records'),
        ),
        migrations.AddField(
            model_name='ramsdocument',
            name='ai_review',
            field=models.JSONField(blank=True, null=True, help_text='AI safety review output: {summary, findings: [{severity, section, issue, recommendation}], reviewed_at}'),
        ),
    ]

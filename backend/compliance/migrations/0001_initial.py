import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ComplianceCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('max_score', models.IntegerField(default=10)),
                ('current_score', models.IntegerField(default=0)),
                ('notes', models.TextField(blank=True, default='')),
                ('order', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Compliance Category',
                'verbose_name_plural': 'Compliance Categories',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='IncidentReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('severity', models.CharField(choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('CRITICAL', 'Critical')], db_index=True, default='MEDIUM', max_length=20)),
                ('status', models.CharField(choices=[('OPEN', 'Open'), ('INVESTIGATING', 'Investigating'), ('RESOLVED', 'Resolved'), ('CLOSED', 'Closed')], db_index=True, default='OPEN', max_length=20)),
                ('location', models.CharField(blank=True, default='', max_length=255)),
                ('incident_date', models.DateTimeField(db_index=True)),
                ('resolution_notes', models.TextField(blank=True, default='')),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_incidents', to=settings.AUTH_USER_MODEL)),
                ('reported_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reported_incidents', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Incident Report',
                'verbose_name_plural': 'Incident Reports',
                'ordering': ['-incident_date'],
            },
        ),
        migrations.CreateModel(
            name='PeaceOfMindScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField(default=0)),
                ('previous_score', models.IntegerField(default=0)),
                ('total_items', models.IntegerField(default=0)),
                ('compliant_count', models.IntegerField(default=0)),
                ('due_soon_count', models.IntegerField(default=0)),
                ('overdue_count', models.IntegerField(default=0)),
                ('legal_items', models.IntegerField(default=0)),
                ('best_practice_items', models.IntegerField(default=0)),
                ('last_calculated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Peace of Mind Score',
                'verbose_name_plural': 'Peace of Mind Score',
            },
        ),
        migrations.CreateModel(
            name='RiskAssessment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('site_area', models.CharField(help_text='Area or location assessed', max_length=255)),
                ('assessment_date', models.DateField()),
                ('review_date', models.DateField(help_text='Next review due date')),
                ('status', models.CharField(choices=[('CURRENT', 'Current'), ('REVIEW_DUE', 'Review Due'), ('EXPIRED', 'Expired'), ('DRAFT', 'Draft')], db_index=True, default='CURRENT', max_length=20)),
                ('description', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assessor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assessments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Risk Assessment',
                'verbose_name_plural': 'Risk Assessments',
                'ordering': ['-assessment_date'],
            },
        ),
        migrations.CreateModel(
            name='ScoreAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField()),
                ('previous_score', models.IntegerField()),
                ('total_items', models.IntegerField()),
                ('compliant_count', models.IntegerField()),
                ('due_soon_count', models.IntegerField()),
                ('overdue_count', models.IntegerField()),
                ('trigger', models.CharField(choices=[('auto', 'Automatic (item change)'), ('manual', 'Manual recalculation'), ('scheduled', 'Scheduled (daily)')], default='auto', max_length=20)),
                ('calculated_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Score Audit Log',
                'verbose_name_plural': 'Score Audit Logs',
                'ordering': ['-calculated_at'],
            },
        ),
        migrations.CreateModel(
            name='Equipment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('location', models.CharField(max_length=255)),
                ('category', models.CharField(choices=[('FIRE_SAFETY', 'Fire Safety'), ('FIRST_AID', 'First Aid'), ('ELECTRICAL', 'Electrical'), ('VENTILATION', 'Ventilation'), ('SECURITY', 'Security'), ('WELLNESS', 'Wellness Equipment'), ('OTHER', 'Other')], db_index=True, default='OTHER', max_length=30)),
                ('serial_number', models.CharField(blank=True, default='', max_length=100)),
                ('last_inspection', models.DateField(blank=True, null=True)),
                ('next_inspection', models.DateField(blank=True, db_index=True, null=True)),
                ('status', models.CharField(choices=[('OK', 'OK'), ('DUE_SOON', 'Inspection Due Soon'), ('OVERDUE', 'Overdue'), ('OUT_OF_SERVICE', 'Out of Service')], db_index=True, default='OK', max_length=20)),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Equipment',
                'verbose_name_plural': 'Equipment',
                'ordering': ['next_inspection'],
            },
        ),
        migrations.CreateModel(
            name='EquipmentInspection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inspection_date', models.DateField()),
                ('result', models.CharField(choices=[('PASS', 'Pass'), ('FAIL', 'Fail'), ('ADVISORY', 'Advisory')], default='PASS', max_length=20)),
                ('notes', models.TextField(blank=True, default='')),
                ('next_due', models.DateField(blank=True, help_text='Sets next inspection date on equipment', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('equipment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inspections', to='compliance.equipment')),
                ('inspector', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Equipment Inspection',
                'verbose_name_plural': 'Equipment Inspections',
                'ordering': ['-inspection_date'],
            },
        ),
        migrations.CreateModel(
            name='HazardFinding',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(help_text='e.g. Fire Safety, Slips/Trips, Chemical Handling', max_length=255)),
                ('description', models.TextField()),
                ('severity', models.CharField(choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('CRITICAL', 'Critical')], db_index=True, default='MEDIUM', max_length=20)),
                ('confidence', models.FloatField(default=1.0, help_text='Confidence level 0.0\u20131.0')),
                ('control_measures', models.TextField(blank=True, default='', help_text='Control measures, one per line')),
                ('regulatory_ref', models.CharField(blank=True, default='', help_text='e.g. HSE INDG225, COSHH Reg 7', max_length=255)),
                ('evidence_url', models.URLField(blank=True, default='')),
                ('status', models.CharField(choices=[('OPEN', 'Open'), ('IN_PROGRESS', 'In Progress'), ('RESOLVED', 'Resolved'), ('ACCEPTED', 'Risk Accepted')], db_index=True, default='OPEN', max_length=20)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_findings', to=settings.AUTH_USER_MODEL)),
                ('assessment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='findings', to='compliance.riskassessment')),
            ],
            options={
                'verbose_name': 'Hazard Finding',
                'verbose_name_plural': 'Hazard Findings',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='IncidentPhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='compliance/incidents/%Y/%m/')),
                ('caption', models.CharField(blank=True, default='', max_length=255)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('incident', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photos', to='compliance.incidentreport')),
                ('uploaded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Incident Photo',
                'verbose_name_plural': 'Incident Photos',
            },
        ),
        migrations.CreateModel(
            name='SignOff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(blank=True, default='', max_length=100)),
                ('notes', models.TextField(blank=True, default='')),
                ('signed_at', models.DateTimeField(auto_now_add=True)),
                ('incident', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sign_offs', to='compliance.incidentreport')),
                ('signed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Sign Off',
                'verbose_name_plural': 'Sign Offs',
                'ordering': ['-signed_at'],
            },
        ),
        migrations.CreateModel(
            name='RAMSDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('reference_number', models.CharField(blank=True, db_index=True, default='', max_length=100)),
                ('description', models.TextField(blank=True, default='')),
                ('document', models.FileField(upload_to='compliance/rams/%Y/%m/')),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('ACTIVE', 'Active'), ('EXPIRED', 'Expired'), ('ARCHIVED', 'Archived')], db_index=True, default='DRAFT', max_length=20)),
                ('issue_date', models.DateField(blank=True, null=True)),
                ('expiry_date', models.DateField(blank=True, db_index=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_rams', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'RAMS Document',
                'verbose_name_plural': 'RAMS Documents',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ComplianceItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('item_type', models.CharField(choices=[('LEGAL', 'Legal Requirement'), ('BEST_PRACTICE', 'Best Practice')], db_index=True, default='BEST_PRACTICE', max_length=20)),
                ('status', models.CharField(choices=[('COMPLIANT', 'Compliant'), ('DUE_SOON', 'Due Soon'), ('OVERDUE', 'Overdue')], db_index=True, default='COMPLIANT', max_length=20)),
                ('due_date', models.DateField(blank=True, db_index=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('regulatory_ref', models.CharField(blank=True, default='', help_text='Legal/regulatory reference', max_length=255)),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='compliance.compliancecategory')),
            ],
            options={
                'verbose_name': 'Compliance Item',
                'verbose_name_plural': 'Compliance Items',
                'ordering': ['category', 'item_type', 'title'],
            },
        ),
    ]

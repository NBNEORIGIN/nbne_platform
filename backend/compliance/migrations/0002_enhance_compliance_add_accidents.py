# Generated manually

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("compliance", "0001_initial"),
    ]

    operations = [
        # New fields on ComplianceItem
        migrations.AddField(
            model_name="complianceitem",
            name="frequency_type",
            field=models.CharField(
                choices=[
                    ("monthly", "Monthly"),
                    ("quarterly", "Quarterly"),
                    ("annual", "Annual"),
                    ("biennial", "Every 2 Years"),
                    ("5_year", "Every 5 Years"),
                    ("ad_hoc", "Ad Hoc / One-off"),
                ],
                default="annual",
                db_index=True,
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="complianceitem",
            name="legal_reference",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Full legal reference e.g. Regulatory Reform (Fire Safety) Order 2005",
                max_length=500,
            ),
        ),
        migrations.AddField(
            model_name="complianceitem",
            name="last_completed_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="complianceitem",
            name="next_due_date",
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="complianceitem",
            name="evidence_required",
            field=models.BooleanField(
                default=False,
                help_text="Whether evidence upload is required on completion",
            ),
        ),
        migrations.AddField(
            model_name="complianceitem",
            name="document",
            field=models.FileField(
                blank=True,
                help_text="Latest evidence document",
                null=True,
                upload_to="compliance/evidence/%Y/%m/",
            ),
        ),
        migrations.AddField(
            model_name="complianceitem",
            name="completed_by",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Name of person who completed",
                max_length=255,
            ),
        ),
        # AccidentReport model
        migrations.CreateModel(
            name="AccidentReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(db_index=True)),
                ("time", models.TimeField(blank=True, null=True)),
                ("location", models.CharField(blank=True, default="", max_length=255)),
                ("person_involved", models.CharField(help_text="Name of person involved", max_length=255)),
                ("person_role", models.CharField(blank=True, default="", help_text="e.g. Staff, Client, Visitor", max_length=100)),
                ("description", models.TextField(help_text="Full description of the accident/incident")),
                ("severity", models.CharField(choices=[("MINOR", "Minor (First Aid)"), ("MODERATE", "Moderate (Medical Attention)"), ("MAJOR", "Major (Hospital)"), ("FATAL", "Fatal")], db_index=True, default="MINOR", max_length=20)),
                ("status", models.CharField(choices=[("OPEN", "Open"), ("INVESTIGATING", "Under Investigation"), ("FOLLOW_UP", "Follow-up Required"), ("CLOSED", "Closed")], db_index=True, default="OPEN", max_length=20)),
                ("riddor_reportable", models.BooleanField(default=False, help_text="Is this reportable under RIDDOR?")),
                ("hse_reference", models.CharField(blank=True, default="", help_text="HSE reference number if reported", max_length=100)),
                ("riddor_reported_date", models.DateField(blank=True, null=True)),
                ("follow_up_required", models.BooleanField(default=False)),
                ("follow_up_notes", models.TextField(blank=True, default="")),
                ("follow_up_completed", models.BooleanField(default=False)),
                ("follow_up_completed_date", models.DateField(blank=True, null=True)),
                ("document", models.FileField(blank=True, null=True, upload_to="compliance/accidents/%Y/%m/")),
                ("reported_by", models.CharField(blank=True, default="", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Accident Report",
                "verbose_name_plural": "Accident Reports",
                "ordering": ["-date", "-time"],
            },
        ),
    ]

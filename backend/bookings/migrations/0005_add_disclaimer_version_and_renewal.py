# Generated manually

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0004_classpackage_intakewellbeingdisclaimer_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="intakeprofile",
            name="disclaimer_version",
            field=models.ForeignKey(
                blank=True,
                help_text="Which disclaimer version was signed",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="signed_profiles",
                to="bookings.intakewellbeingdisclaimer",
            ),
        ),
        migrations.AddField(
            model_name="intakeprofile",
            name="renewal_required",
            field=models.BooleanField(
                default=False,
                help_text="Owner has flagged this client to re-sign on next booking",
            ),
        ),
    ]

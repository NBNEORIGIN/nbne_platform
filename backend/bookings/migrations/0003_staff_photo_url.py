# Generated migration for staff photo_url field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0002_schedule_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='staff',
            name='photo_url',
            field=models.URLField(blank=True, help_text='URL to staff member photo'),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0019_classtype_classsession'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='long_description',
            field=models.TextField(blank=True, default='', help_text='Detailed description (supports HTML) for the service detail page'),
        ),
        migrations.AddField(
            model_name='service',
            name='brochure',
            field=models.FileField(blank=True, help_text='Downloadable brochure or course document (PDF)', null=True, upload_to='services/brochures/%Y/%m/'),
        ),
        migrations.AddField(
            model_name='service',
            name='brochure_filename',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='service',
            name='description',
            field=models.TextField(blank=True, help_text='Short description shown in listings and cards'),
        ),
    ]

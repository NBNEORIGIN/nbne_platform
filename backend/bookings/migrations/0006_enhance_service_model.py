from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0005_add_disclaimer_version_and_renewal'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='category',
            field=models.CharField(blank=True, default='', help_text='e.g. Mindfulness, Group, Corporate', max_length=100),
        ),
        migrations.AddField(
            model_name='service',
            name='payment_type',
            field=models.CharField(choices=[('full', 'Full Payment'), ('deposit', 'Deposit Required'), ('free', 'Free / No Payment')], default='full', max_length=20),
        ),
        migrations.AddField(
            model_name='service',
            name='deposit_pence',
            field=models.IntegerField(default=0, help_text='Fixed deposit amount in pence'),
        ),
        migrations.AddField(
            model_name='service',
            name='deposit_percentage',
            field=models.IntegerField(default=0, help_text='Deposit as percentage of price', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AddField(
            model_name='service',
            name='colour',
            field=models.CharField(blank=True, default='', help_text='Hex colour for calendar display', max_length=7),
        ),
        migrations.AddField(
            model_name='service',
            name='sort_order',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterModelOptions(
            name='service',
            options={'ordering': ['sort_order', 'name']},
        ),
    ]

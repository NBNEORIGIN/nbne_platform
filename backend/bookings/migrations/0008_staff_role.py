from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0007_staffblock'),
    ]

    operations = [
        migrations.AddField(
            model_name='staff',
            name='role',
            field=models.CharField(choices=[('staff', 'Staff'), ('manager', 'Manager'), ('owner', 'Owner')], default='staff', max_length=20),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compliance', '0004_backfill_tenant_nonnull'),
    ]

    operations = [
        migrations.AddField(
            model_name='complianceitem',
            name='expiry_date',
            field=models.DateField(blank=True, db_index=True, help_text='When this item expires (e.g. insurance renewal date)', null=True),
        ),
        migrations.AddField(
            model_name='complianceitem',
            name='reminder_days',
            field=models.IntegerField(default=30, help_text='Days before expiry to start reminding'),
        ),
        migrations.AddField(
            model_name='complianceitem',
            name='plain_english_why',
            field=models.CharField(blank=True, default='', help_text='Why this matters in plain English', max_length=500),
        ),
        migrations.AddField(
            model_name='complianceitem',
            name='primary_action',
            field=models.CharField(blank=True, default='', help_text='Primary action label e.g. Upload document, Book testing', max_length=100),
        ),
    ]

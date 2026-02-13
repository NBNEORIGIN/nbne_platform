from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Lead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('source', models.CharField(choices=[('booking', 'Booking'), ('website', 'Website'), ('referral', 'Referral'), ('social', 'Social Media'), ('manual', 'Manual Entry'), ('other', 'Other')], default='manual', max_length=30)),
                ('status', models.CharField(choices=[('NEW', 'New'), ('CONTACTED', 'Contacted'), ('QUALIFIED', 'Qualified'), ('CONVERTED', 'Converted'), ('LOST', 'Lost')], default='NEW', max_length=20)),
                ('value_pence', models.IntegerField(default=0, help_text='Estimated value in pence')),
                ('notes', models.TextField(blank=True)),
                ('client_id', models.IntegerField(blank=True, help_text='bookings.Client FK', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]

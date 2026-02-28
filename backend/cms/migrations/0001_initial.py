import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('slug', models.SlugField(help_text='URL-friendly identifier, e.g. "about" or "home"', max_length=200)),
                ('content', models.TextField(blank=True, default='', help_text='Rich HTML content for the page body')),
                ('hero_image', models.ImageField(blank=True, null=True, upload_to='cms/heroes/%Y/%m/')),
                ('hero_headline', models.CharField(blank=True, default='', max_length=300)),
                ('hero_subheadline', models.CharField(blank=True, default='', max_length=500)),
                ('meta_title', models.CharField(blank=True, default='', help_text='SEO title (falls back to title)', max_length=200)),
                ('meta_description', models.TextField(blank=True, default='', help_text='SEO meta description', max_length=500)),
                ('is_published', models.BooleanField(db_index=True, default=False)),
                ('sort_order', models.IntegerField(default=0)),
                ('show_in_nav', models.BooleanField(default=True, help_text='Show this page in the site navigation')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cms_pages', to='tenants.tenantsettings')),
            ],
            options={
                'ordering': ['sort_order', 'title'],
                'unique_together': {('tenant', 'slug')},
            },
        ),
        migrations.CreateModel(
            name='PageImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='cms/pages/%Y/%m/')),
                ('alt_text', models.CharField(blank=True, default='', max_length=300)),
                ('caption', models.CharField(blank=True, default='', max_length=500)),
                ('sort_order', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('page', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='cms.page')),
            ],
            options={
                'ordering': ['sort_order', 'created_at'],
            },
        ),
        migrations.CreateModel(
            name='BlogPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=300)),
                ('slug', models.SlugField(help_text='URL-friendly identifier', max_length=300)),
                ('excerpt', models.TextField(blank=True, default='', help_text='Short summary shown in listings', max_length=500)),
                ('content', models.TextField(blank=True, default='', help_text='Rich HTML content')),
                ('featured_image', models.ImageField(blank=True, null=True, upload_to='cms/blog/%Y/%m/')),
                ('featured_image_alt', models.CharField(blank=True, default='', max_length=300)),
                ('author_name', models.CharField(blank=True, default='', max_length=200)),
                ('category', models.CharField(blank=True, default='', max_length=100)),
                ('tags', models.CharField(blank=True, default='', help_text='Comma-separated tags', max_length=500)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('published', 'Published')], db_index=True, default='draft', max_length=20)),
                ('meta_title', models.CharField(blank=True, default='', help_text='SEO title', max_length=200)),
                ('meta_description', models.TextField(blank=True, default='', help_text='SEO meta description', max_length=500)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blog_posts', to='tenants.tenantsettings')),
            ],
            options={
                'ordering': ['-published_at', '-created_at'],
                'unique_together': {('tenant', 'slug')},
            },
        ),
    ]

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='subtitle',
            field=models.CharField(blank=True, default='', help_text='Short tagline shown below the title', max_length=255),
        ),
        migrations.AddField(
            model_name='product',
            name='compare_at_price',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Original price for showing discounts', max_digits=10, null=True),
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='shop/products/%Y/%m/')),
                ('alt_text', models.CharField(blank=True, default='', max_length=255)),
                ('sort_order', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='shop.product')),
            ],
            options={
                'db_table': 'shop_product_image',
                'ordering': ['sort_order', 'id'],
            },
        ),
    ]

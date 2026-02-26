from django.db import models
from django.core.validators import MinValueValidator


class Product(models.Model):
    """A physical or digital product for sale in the tenant's shop."""
    tenant = models.ForeignKey(
        'tenants.TenantSettings', on_delete=models.CASCADE, related_name='products'
    )
    name = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True, default='', help_text='Short tagline shown below the title')
    description = models.TextField(blank=True, default='')
    category = models.CharField(max_length=100, blank=True, default='', help_text='e.g. First Aid Kits, Fire Safety, PPE')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Original price for showing discounts')
    image_url = models.URLField(blank=True, default='', help_text='Legacy single image URL')
    stock_quantity = models.IntegerField(default=0, help_text='Current stock level')
    track_stock = models.BooleanField(default=False, help_text='Enable stock tracking')
    sort_order = models.IntegerField(default=0)
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shop_product'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.name} (£{self.price})"

    @property
    def price_pence(self):
        return int(self.price * 100)

    @property
    def in_stock(self):
        if not self.track_stock:
            return True
        return self.stock_quantity > 0

    @property
    def primary_image_url(self):
        """Return the first uploaded image URL, or legacy image_url fallback."""
        first = self.images.order_by('sort_order', 'id').first()
        if first and first.image:
            return first.image.url
        return self.image_url or ''


class ProductImage(models.Model):
    """An image attached to a product. Supports multiple images per product."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='shop/products/%Y/%m/')
    alt_text = models.CharField(max_length=255, blank=True, default='')
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shop_product_image'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"Image for {self.product.name} (#{self.sort_order})"


class Order(models.Model):
    """A customer order for one or more products."""
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    tenant = models.ForeignKey(
        'tenants.TenantSettings', on_delete=models.CASCADE, related_name='orders'
    )
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=50, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_pence = models.IntegerField(default=0)
    stripe_session_id = models.CharField(max_length=255, blank=True, default='')
    stripe_payment_intent = models.CharField(max_length=255, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shop_order'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} — {self.customer_name} (£{self.total_pence / 100:.2f})"


class OrderItem(models.Model):
    """A line item in an order."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=255, help_text='Snapshot of product name at time of order')
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price_pence = models.IntegerField(default=0)

    class Meta:
        db_table = 'shop_order_item'

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

    @property
    def line_total_pence(self):
        return self.quantity * self.unit_price_pence

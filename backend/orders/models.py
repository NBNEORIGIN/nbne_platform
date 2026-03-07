import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


DATA_ORIGIN_CHOICES = [
    ('REAL', 'Real'),
    ('DEMO', 'Demo'),
]


class MenuCategory(models.Model):
    """Category grouping for menu items (e.g. Pizzas, Sides, Desserts, Drinks)."""
    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, related_name='menu_categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    sort_order = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    icon = models.CharField(max_length=50, blank=True, default='', help_text='Emoji or icon name')
    data_origin = models.CharField(max_length=4, choices=DATA_ORIGIN_CHOICES, default='REAL', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'Menu categories'
        unique_together = ['tenant', 'name']

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    """Individual item on the menu (e.g. Margherita, Garlic Bread, Tiramisu)."""
    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, related_name='menu_items')
    category = models.ForeignKey(MenuCategory, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='', help_text='Short description shown on menu')
    price_pence = models.IntegerField(validators=[MinValueValidator(0)], help_text='Price in pence')
    image_url = models.URLField(blank=True, default='')
    sort_order = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    sold_out = models.BooleanField(default=False, help_text='Temporarily unavailable')
    # Prep time estimate for wait time calculation
    prep_time_minutes = models.IntegerField(default=10, help_text='Estimated prep time in minutes')
    # Dietary/allergen flags
    vegetarian = models.BooleanField(default=False)
    vegan = models.BooleanField(default=False)
    gluten_free = models.BooleanField(default=False)
    # Analytics fields
    total_ordered = models.IntegerField(default=0)
    total_revenue_pence = models.IntegerField(default=0)
    data_origin = models.CharField(max_length=4, choices=DATA_ORIGIN_CHOICES, default='REAL', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category__sort_order', 'sort_order', 'name']

    def __str__(self):
        return f"{self.name} (£{self.price_pence / 100:.2f})"

    @property
    def price_display(self):
        return f"£{self.price_pence / 100:.2f}"


class Order(models.Model):
    """A customer order containing one or more items."""
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Collection'),
        ('collected', 'Collected'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Card (Stripe)'),
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('unpaid', 'Not Yet Paid'),
    ]
    ORDER_SOURCE_CHOICES = [
        ('online', 'Online Order'),
        ('phone', 'Phone Order'),
        ('walkin', 'Walk-in'),
    ]

    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, related_name='orders')
    # Public-facing order reference (short, human-readable)
    order_ref = models.CharField(max_length=10, db_index=True)
    # Customer details (no login required)
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=50, blank=True, default='')
    customer_email = models.CharField(max_length=200, blank=True, default='')
    # Order workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    source = models.CharField(max_length=10, choices=ORDER_SOURCE_CHOICES, default='online')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='unpaid')
    payment_confirmed = models.BooleanField(default=False)
    stripe_session_id = models.CharField(max_length=255, blank=True, default='')
    # Financials
    subtotal_pence = models.IntegerField(default=0)
    total_pence = models.IntegerField(default=0)
    # Timing
    estimated_ready_minutes = models.IntegerField(default=0, help_text='Estimated minutes until ready')
    estimated_ready_at = models.DateTimeField(null=True, blank=True)
    # Notes
    notes = models.TextField(blank=True, default='', help_text='Special instructions from customer')
    kitchen_notes = models.TextField(blank=True, default='', help_text='Internal notes for kitchen')
    # Timestamps
    placed_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True, help_text='When kitchen started preparing')
    ready_at = models.DateTimeField(null=True, blank=True, help_text='When marked as ready')
    collected_at = models.DateTimeField(null=True, blank=True, help_text='When customer collected')
    cancelled_at = models.DateTimeField(null=True, blank=True)
    # Tracking
    data_origin = models.CharField(max_length=4, choices=DATA_ORIGIN_CHOICES, default='REAL', db_index=True)
    demo_seed_id = models.UUIDField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ['-placed_at']

    def __str__(self):
        return f"Order #{self.order_ref} — {self.customer_name} ({self.get_status_display()})"

    @property
    def total_display(self):
        return f"£{self.total_pence / 100:.2f}"

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    def calculate_totals(self):
        """Recalculate subtotal and total from order items."""
        self.subtotal_pence = sum(
            item.quantity * item.unit_price_pence for item in self.items.all()
        )
        self.total_pence = self.subtotal_pence  # No tax/discount for now

    def transition_status(self, new_status):
        """Move order to a new status with timestamp tracking."""
        now = timezone.now()
        if new_status == 'preparing' and not self.started_at:
            self.started_at = now
        elif new_status == 'ready' and not self.ready_at:
            self.ready_at = now
        elif new_status == 'collected' and not self.collected_at:
            self.collected_at = now
        elif new_status == 'cancelled' and not self.cancelled_at:
            self.cancelled_at = now
        self.status = new_status
        self.save()


class OrderItem(models.Model):
    """Line item within an order."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT, related_name='order_items')
    name = models.CharField(max_length=200, help_text='Snapshot of item name at time of order')
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price_pence = models.IntegerField(help_text='Snapshot of price at time of order')
    notes = models.CharField(max_length=500, blank=True, default='', help_text='Item-level special requests')

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.quantity}x {self.name}"

    @property
    def line_total_pence(self):
        return self.quantity * self.unit_price_pence


class OrderQueueSettings(models.Model):
    """Per-tenant settings for the order queue / kitchen display."""
    tenant = models.OneToOneField('tenants.TenantSettings', on_delete=models.CASCADE, related_name='order_queue_settings')
    # Current wait time (manually adjustable by owner)
    current_wait_minutes = models.IntegerField(default=15)
    auto_calculate_wait = models.BooleanField(default=True, help_text='Auto-calculate from queue depth')
    avg_prep_time_minutes = models.IntegerField(default=12, help_text='Average prep time per order')
    max_concurrent_orders = models.IntegerField(default=5, help_text='How many orders kitchen can handle at once')
    # Accepting orders toggle
    accepting_orders = models.BooleanField(default=True)
    not_accepting_reason = models.CharField(max_length=200, blank=True, default='')
    # Opening hours for order system
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    # Seasonal
    seasonal_closed = models.BooleanField(default=False, help_text='Closed for the season')
    seasonal_message = models.CharField(max_length=500, blank=True, default='')
    # Payment info (bank transfer details for blackboard equivalent)
    bank_transfer_details = models.TextField(blank=True, default='', help_text='Bank name, sort code, account number')
    # Accept various payment methods
    accept_card = models.BooleanField(default=True)
    accept_cash = models.BooleanField(default=True)
    accept_bank_transfer = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Order Queue Settings'
        verbose_name_plural = 'Order Queue Settings'

    def __str__(self):
        return f"Queue settings for {self.tenant}"

    def calculate_wait_time(self):
        """Calculate estimated wait based on active orders."""
        if not self.auto_calculate_wait:
            return self.current_wait_minutes
        active_orders = Order.objects.filter(
            tenant=self.tenant,
            status__in=['received', 'preparing'],
        ).count()
        # Simple formula: orders in queue / concurrent capacity * avg prep time
        if self.max_concurrent_orders <= 0:
            return self.avg_prep_time_minutes
        batches = (active_orders + self.max_concurrent_orders - 1) // self.max_concurrent_orders
        return max(self.avg_prep_time_minutes, batches * self.avg_prep_time_minutes)


class DailyOrderSummary(models.Model):
    """Pre-aggregated daily stats for analytics and procurement prediction."""
    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, related_name='daily_order_summaries')
    date = models.DateField()
    total_orders = models.IntegerField(default=0)
    total_revenue_pence = models.IntegerField(default=0)
    total_items_sold = models.IntegerField(default=0)
    avg_order_value_pence = models.IntegerField(default=0)
    peak_hour = models.IntegerField(null=True, blank=True, help_text='Hour with most orders (0-23)')
    cancelled_orders = models.IntegerField(default=0)
    avg_wait_minutes = models.FloatField(default=0)
    # Weather (optional, for correlation)
    weather_temp_c = models.FloatField(null=True, blank=True)
    weather_condition = models.CharField(max_length=50, blank=True, default='')
    # Flags
    is_school_holiday = models.BooleanField(default=False)
    is_bank_holiday = models.BooleanField(default=False)
    is_weekend = models.BooleanField(default=False)
    holiday_name = models.CharField(max_length=100, blank=True, default='')
    # Day of week (0=Mon, 6=Sun)
    day_of_week = models.IntegerField(default=0)
    # Week number in year
    week_number = models.IntegerField(default=0)
    data_origin = models.CharField(max_length=4, choices=DATA_ORIGIN_CHOICES, default='REAL', db_index=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['tenant', 'date']
        verbose_name_plural = 'Daily order summaries'

    def __str__(self):
        return f"{self.date} — {self.total_orders} orders"


class ItemDailySales(models.Model):
    """Per-item daily sales for procurement prediction."""
    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, related_name='item_daily_sales')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='daily_sales')
    date = models.DateField()
    quantity_sold = models.IntegerField(default=0)
    revenue_pence = models.IntegerField(default=0)
    # Contextual flags (denormalised for fast queries)
    is_school_holiday = models.BooleanField(default=False)
    is_bank_holiday = models.BooleanField(default=False)
    is_weekend = models.BooleanField(default=False)
    day_of_week = models.IntegerField(default=0)
    week_number = models.IntegerField(default=0)
    data_origin = models.CharField(max_length=4, choices=DATA_ORIGIN_CHOICES, default='REAL', db_index=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['tenant', 'menu_item', 'date']
        verbose_name_plural = 'Item daily sales'

    def __str__(self):
        return f"{self.menu_item.name} — {self.date} — {self.quantity_sold} sold"

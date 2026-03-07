from rest_framework import serializers
from .models import MenuCategory, MenuItem, Order, OrderItem, OrderQueueSettings, DailyOrderSummary, ItemDailySales


class MenuItemSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = MenuItem
        fields = [
            'id', 'category', 'category_name', 'name', 'description',
            'price_pence', 'price', 'image_url', 'sort_order', 'active',
            'sold_out', 'prep_time_minutes',
            'vegetarian', 'vegan', 'gluten_free',
            'total_ordered', 'total_revenue_pence',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['total_ordered', 'total_revenue_pence']

    def get_price(self, obj):
        return f"{obj.price_pence / 100:.2f}"


class MenuCategorySerializer(serializers.ModelSerializer):
    items = MenuItemSerializer(many=True, read_only=True)

    class Meta:
        model = MenuCategory
        fields = [
            'id', 'name', 'description', 'sort_order', 'active', 'icon',
            'items', 'created_at', 'updated_at',
        ]


class MenuCategoryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer without nested items."""
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = MenuCategory
        fields = ['id', 'name', 'description', 'sort_order', 'active', 'icon', 'item_count']

    def get_item_count(self, obj):
        return obj.items.filter(active=True).count()


class OrderItemSerializer(serializers.ModelSerializer):
    line_total_pence = serializers.IntegerField(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'menu_item', 'name', 'quantity',
            'unit_price_pence', 'notes', 'line_total_pence',
        ]
        read_only_fields = ['name', 'unit_price_pence', 'line_total_pence']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    total_display = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    # Minutes since order was placed
    minutes_ago = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_ref', 'customer_name', 'customer_phone', 'customer_email',
            'status', 'status_display', 'source', 'source_display',
            'payment_method', 'payment_method_display', 'payment_confirmed',
            'subtotal_pence', 'total_pence', 'total_display',
            'estimated_ready_minutes', 'estimated_ready_at',
            'notes', 'kitchen_notes',
            'placed_at', 'started_at', 'ready_at', 'collected_at', 'cancelled_at',
            'items', 'item_count', 'minutes_ago',
        ]
        read_only_fields = [
            'order_ref', 'subtotal_pence', 'total_pence',
            'placed_at', 'started_at', 'ready_at', 'collected_at', 'cancelled_at',
        ]

    def get_minutes_ago(self, obj):
        from django.utils import timezone
        if obj.placed_at:
            delta = timezone.now() - obj.placed_at
            return int(delta.total_seconds() / 60)
        return 0


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating a new order from the customer-facing page."""
    customer_name = serializers.CharField(max_length=200)
    customer_phone = serializers.CharField(max_length=50, required=False, default='', allow_blank=True)
    customer_email = serializers.CharField(max_length=200, required=False, default='', allow_blank=True)
    notes = serializers.CharField(required=False, default='', allow_blank=True)
    payment_method = serializers.ChoiceField(
        choices=['card', 'cash', 'bank_transfer'],
        default='cash',
    )
    source = serializers.ChoiceField(
        choices=['online', 'phone', 'walkin'],
        default='online',
    )
    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        help_text='List of {menu_item_id, quantity, notes?}',
    )


class OrderQueueSettingsSerializer(serializers.ModelSerializer):
    calculated_wait_minutes = serializers.SerializerMethodField()
    active_order_count = serializers.SerializerMethodField()

    class Meta:
        model = OrderQueueSettings
        fields = [
            'current_wait_minutes', 'auto_calculate_wait',
            'avg_prep_time_minutes', 'max_concurrent_orders',
            'accepting_orders', 'not_accepting_reason',
            'opening_time', 'closing_time',
            'seasonal_closed', 'seasonal_message',
            'bank_transfer_details',
            'accept_card', 'accept_cash', 'accept_bank_transfer',
            'calculated_wait_minutes', 'active_order_count',
            'updated_at',
        ]

    def get_calculated_wait_minutes(self, obj):
        return obj.calculate_wait_time()

    def get_active_order_count(self, obj):
        return Order.objects.filter(
            tenant=obj.tenant,
            status__in=['received', 'preparing'],
        ).count()


class DailyOrderSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyOrderSummary
        fields = [
            'id', 'date', 'total_orders', 'total_revenue_pence',
            'total_items_sold', 'avg_order_value_pence', 'peak_hour',
            'cancelled_orders', 'avg_wait_minutes',
            'is_school_holiday', 'is_bank_holiday', 'is_weekend',
            'holiday_name', 'day_of_week', 'week_number',
        ]


class ItemDailySalesSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='menu_item.name', read_only=True)

    class Meta:
        model = ItemDailySales
        fields = [
            'id', 'menu_item', 'item_name', 'date',
            'quantity_sold', 'revenue_pence',
            'is_school_holiday', 'is_bank_holiday', 'is_weekend',
            'day_of_week', 'week_number',
        ]

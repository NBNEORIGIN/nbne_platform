from django.contrib import admin
from .models import Product, ProductImage, Order, OrderItem


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'sort_order']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'quantity', 'unit_price_pence', 'line_total_pence']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'subtitle', 'category', 'price', 'stock_quantity', 'track_stock', 'active', 'created_at']
    list_filter = ['active', 'category', 'track_stock']
    search_fields = ['name', 'subtitle', 'description', 'category']
    list_editable = ['active']
    inlines = [ProductImageInline]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'customer_email', 'status', 'total_display', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['customer_name', 'customer_email']
    inlines = [OrderItemInline]
    readonly_fields = ['stripe_session_id', 'stripe_payment_intent']

    def total_display(self, obj):
        return f"£{obj.total_pence / 100:.2f}"
    total_display.short_description = 'Total'

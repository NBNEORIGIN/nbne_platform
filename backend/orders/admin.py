from django.contrib import admin
from .models import (
    MenuCategory, MenuItem, Order, OrderItem,
    OrderQueueSettings, DailyOrderSummary, ItemDailySales,
)


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 0
    fields = ['name', 'price_pence', 'sort_order', 'active', 'sold_out', 'vegetarian', 'vegan', 'gluten_free']


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'tenant', 'sort_order', 'active']
    list_filter = ['tenant', 'active']
    inlines = [MenuItemInline]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price_pence', 'active', 'sold_out', 'total_ordered']
    list_filter = ['tenant', 'category', 'active', 'sold_out', 'vegetarian', 'vegan', 'gluten_free']
    search_fields = ['name']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['name', 'unit_price_pence', 'line_total_pence']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_ref', 'customer_name', 'status', 'total_pence', 'source', 'payment_method', 'placed_at']
    list_filter = ['tenant', 'status', 'source', 'payment_method', 'payment_confirmed']
    search_fields = ['order_ref', 'customer_name', 'customer_phone']
    readonly_fields = ['placed_at', 'started_at', 'ready_at', 'collected_at', 'cancelled_at']
    inlines = [OrderItemInline]


@admin.register(OrderQueueSettings)
class OrderQueueSettingsAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'accepting_orders', 'current_wait_minutes', 'seasonal_closed']


@admin.register(DailyOrderSummary)
class DailyOrderSummaryAdmin(admin.ModelAdmin):
    list_display = ['date', 'tenant', 'total_orders', 'total_revenue_pence', 'is_school_holiday', 'is_bank_holiday']
    list_filter = ['tenant', 'is_school_holiday', 'is_bank_holiday']


@admin.register(ItemDailySales)
class ItemDailySalesAdmin(admin.ModelAdmin):
    list_display = ['date', 'menu_item', 'quantity_sold', 'revenue_pence']
    list_filter = ['tenant', 'menu_item']

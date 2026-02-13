from django.contrib import admin
from .models import Config


@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'category', 'updated_at']
    list_filter = ['category']
    search_fields = ['key', 'value']
    readonly_fields = ['created_at', 'updated_at']

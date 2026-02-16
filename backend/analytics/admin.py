from django.contrib import admin
from core.admin_tenant import TenantAdminMixin
from .models import Recommendation


@admin.register(Recommendation)
class RecommendationAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['title', 'recommendation_type', 'priority', 'is_dismissed', 'created_at']
    list_filter = ['recommendation_type', 'is_dismissed']
    search_fields = ['title']

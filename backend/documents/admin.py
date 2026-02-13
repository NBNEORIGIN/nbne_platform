from django.contrib import admin
from .models import Document, DocumentTag


@admin.register(DocumentTag)
class DocumentTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'colour']
    search_fields = ['name']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'access_level', 'status', 'expiry_date', 'is_placeholder', 'created_at']
    list_filter = ['category', 'access_level', 'is_placeholder', 'is_archived']
    search_fields = ['title', 'description', 'regulatory_ref']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['uploaded_by', 'linked_staff', 'compliance_item']

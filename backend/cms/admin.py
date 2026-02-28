from django.contrib import admin
from .models import Page, PageImage, BlogPost


class PageImageInline(admin.TabularInline):
    model = PageImage
    extra = 0


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'tenant', 'is_published', 'sort_order', 'updated_at']
    list_filter = ['tenant', 'is_published']
    search_fields = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [PageImageInline]


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'tenant', 'status', 'category', 'published_at']
    list_filter = ['tenant', 'status', 'category']
    search_fields = ['title', 'slug', 'content']
    prepopulated_fields = {'slug': ('title',)}

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Page(models.Model):
    """Tenant-editable CMS page (hero, about, gallery, etc.)."""
    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, related_name='cms_pages')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, help_text='URL-friendly identifier, e.g. "about" or "home"')
    content = models.TextField(blank=True, default='', help_text='Rich HTML content for the page body')
    hero_image = models.ImageField(upload_to='cms/heroes/%Y/%m/', null=True, blank=True)
    hero_headline = models.CharField(max_length=300, blank=True, default='')
    hero_subheadline = models.CharField(max_length=500, blank=True, default='')
    meta_title = models.CharField(max_length=200, blank=True, default='', help_text='SEO title (falls back to title)')
    meta_description = models.TextField(max_length=500, blank=True, default='', help_text='SEO meta description')
    is_published = models.BooleanField(default=False, db_index=True)
    sort_order = models.IntegerField(default=0)
    show_in_nav = models.BooleanField(default=True, help_text='Show this page in the site navigation')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'title']
        unique_together = [('tenant', 'slug')]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class PageImage(models.Model):
    """Image attached to a CMS page (for galleries, inline images, etc.)."""
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='cms/pages/%Y/%m/')
    alt_text = models.CharField(max_length=300, blank=True, default='')
    caption = models.CharField(max_length=500, blank=True, default='')
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'created_at']

    def __str__(self):
        return f'{self.page.title} — image {self.id}'


class BlogPost(models.Model):
    """Tenant blog post for SEO / content marketing."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, related_name='blog_posts')
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, help_text='URL-friendly identifier')
    excerpt = models.TextField(max_length=500, blank=True, default='', help_text='Short summary shown in listings')
    content = models.TextField(blank=True, default='', help_text='Rich HTML content')
    featured_image = models.ImageField(upload_to='cms/blog/%Y/%m/', null=True, blank=True)
    featured_image_alt = models.CharField(max_length=300, blank=True, default='')
    author_name = models.CharField(max_length=200, blank=True, default='')
    category = models.CharField(max_length=100, blank=True, default='')
    tags = models.CharField(max_length=500, blank=True, default='', help_text='Comma-separated tags')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    meta_title = models.CharField(max_length=200, blank=True, default='', help_text='SEO title')
    meta_description = models.TextField(max_length=500, blank=True, default='', help_text='SEO meta description')
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at', '-created_at']
        unique_together = [('tenant', 'slug')]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

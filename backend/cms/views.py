from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status, serializers
from django.db import IntegrityError
from django.utils import timezone
from .models import Page, PageImage, BlogPost


# ── Serializers ──────────────────────────────────────────────

class PageImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = PageImage
        fields = ['id', 'url', 'alt_text', 'caption', 'sort_order']

    def get_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class PageSerializer(serializers.ModelSerializer):
    images = PageImageSerializer(many=True, read_only=True)
    hero_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ['id', 'title', 'slug', 'content', 'hero_image_url',
                  'hero_headline', 'hero_subheadline',
                  'meta_title', 'meta_description',
                  'is_published', 'sort_order', 'show_in_nav',
                  'images', 'created_at', 'updated_at']

    def get_hero_image_url(self, obj):
        if obj.hero_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.hero_image.url)
            return obj.hero_image.url
        return None


class BlogPostSerializer(serializers.ModelSerializer):
    featured_image_url = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'slug', 'excerpt', 'content',
                  'featured_image_url', 'featured_image_alt',
                  'author_name', 'category', 'tags',
                  'status', 'meta_title', 'meta_description',
                  'published_at', 'created_at', 'updated_at']

    def get_featured_image_url(self, obj):
        if obj.featured_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.featured_image.url)
            return obj.featured_image.url
        return None


# ── CMS Page Views ───────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def page_list(request):
    """List all CMS pages for the current tenant (admin)."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response([], status=200)
    pages = Page.objects.filter(tenant=tenant)
    return Response(PageSerializer(pages, many=True, context={'request': request}).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_pages(request):
    """Public: list published pages for navigation."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response([])
    pages = Page.objects.filter(tenant=tenant, is_published=True)
    return Response(PageSerializer(pages, many=True, context={'request': request}).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_page_detail(request, slug):
    """Public: get a single published page by slug."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=404)
    try:
        page = Page.objects.get(tenant=tenant, slug=slug, is_published=True)
    except Page.DoesNotExist:
        return Response({'error': 'Page not found'}, status=404)
    return Response(PageSerializer(page, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def page_create(request):
    """Create a new CMS page."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=400)
    serializer = PageSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    try:
        serializer.save(tenant=tenant)
    except IntegrityError:
        return Response({'slug': ['A page with this slug already exists for this tenant.']}, status=409)
    return Response(serializer.data, status=201)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def page_detail(request, page_id):
    """Get, update, or delete a CMS page."""
    tenant = getattr(request, 'tenant', None)
    try:
        page = Page.objects.get(id=page_id, tenant=tenant)
    except Page.DoesNotExist:
        return Response({'error': 'Page not found'}, status=404)

    if request.method == 'GET':
        return Response(PageSerializer(page, context={'request': request}).data)

    if request.method == 'DELETE':
        page.delete()
        return Response(status=204)

    # PATCH
    serializer = PageSerializer(page, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    serializer.save()
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def page_upload_hero(request, page_id):
    """Upload hero image for a CMS page."""
    tenant = getattr(request, 'tenant', None)
    try:
        page = Page.objects.get(id=page_id, tenant=tenant)
    except Page.DoesNotExist:
        return Response({'error': 'Page not found'}, status=404)
    f = request.FILES.get('file')
    if not f:
        return Response({'error': 'No file provided'}, status=400)
    page.hero_image = f
    page.save(update_fields=['hero_image'])
    return Response(PageSerializer(page, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def page_upload_image(request, page_id):
    """Upload an image to a CMS page gallery."""
    tenant = getattr(request, 'tenant', None)
    try:
        page = Page.objects.get(id=page_id, tenant=tenant)
    except Page.DoesNotExist:
        return Response({'error': 'Page not found'}, status=404)
    f = request.FILES.get('file')
    if not f:
        return Response({'error': 'No file provided'}, status=400)
    alt = request.data.get('alt_text', '')
    caption = request.data.get('caption', '')
    img = PageImage.objects.create(page=page, image=f, alt_text=alt, caption=caption)
    return Response(PageImageSerializer(img, context={'request': request}).data, status=201)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def page_delete_image(request, page_id, image_id):
    """Delete an image from a CMS page gallery."""
    tenant = getattr(request, 'tenant', None)
    try:
        page = Page.objects.get(id=page_id, tenant=tenant)
        img = PageImage.objects.get(id=image_id, page=page)
    except (Page.DoesNotExist, PageImage.DoesNotExist):
        return Response({'error': 'Not found'}, status=404)
    img.image.delete(save=False)
    img.delete()
    return Response(status=204)


# ── Blog Views ───────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def blog_list(request):
    """List all blog posts for the current tenant (admin)."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response([])
    posts = BlogPost.objects.filter(tenant=tenant)
    return Response(BlogPostSerializer(posts, many=True, context={'request': request}).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_blog_list(request):
    """Public: list published blog posts."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response([])
    posts = BlogPost.objects.filter(tenant=tenant, status='published')
    return Response(BlogPostSerializer(posts, many=True, context={'request': request}).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_blog_detail(request, slug):
    """Public: get a single published blog post by slug."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=404)
    try:
        post = BlogPost.objects.get(tenant=tenant, slug=slug, status='published')
    except BlogPost.DoesNotExist:
        return Response({'error': 'Post not found'}, status=404)
    return Response(BlogPostSerializer(post, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def blog_create(request):
    """Create a new blog post."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=400)
    serializer = BlogPostSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    try:
        post = serializer.save(tenant=tenant)
    except IntegrityError:
        return Response({'slug': ['A blog post with this slug already exists for this tenant.']}, status=409)
    if post.status == 'published' and not post.published_at:
        post.published_at = timezone.now()
        post.save(update_fields=['published_at'])
    return Response(BlogPostSerializer(post, context={'request': request}).data, status=201)



@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def blog_detail(request, post_id):
    """Get, update, or delete a blog post."""
    tenant = getattr(request, 'tenant', None)
    try:
        post = BlogPost.objects.get(id=post_id, tenant=tenant)
    except BlogPost.DoesNotExist:
        return Response({'error': 'Post not found'}, status=404)

    if request.method == 'GET':
        return Response(BlogPostSerializer(post, context={'request': request}).data)

    if request.method == 'DELETE':
        post.delete()
        return Response(status=204)

    # PATCH
    serializer = BlogPostSerializer(post, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    post = serializer.save()
    # Auto-set published_at on first publish
    if post.status == 'published' and not post.published_at:
        post.published_at = timezone.now()
        post.save(update_fields=['published_at'])
    return Response(BlogPostSerializer(post, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def blog_upload_image(request, post_id):
    """Upload featured image for a blog post."""
    tenant = getattr(request, 'tenant', None)
    try:
        post = BlogPost.objects.get(id=post_id, tenant=tenant)
    except BlogPost.DoesNotExist:
        return Response({'error': 'Post not found'}, status=404)
    f = request.FILES.get('file')
    if not f:
        return Response({'error': 'No file provided'}, status=400)
    post.featured_image = f
    post.save(update_fields=['featured_image'])
    return Response(BlogPostSerializer(post, context={'request': request}).data)

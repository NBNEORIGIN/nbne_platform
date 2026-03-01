import logging
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, parser_classes, action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from accounts.permissions import IsManagerOrAbove
from rest_framework.response import Response
from .models import Product, ProductImage, Order, OrderItem
from .serializers import ProductSerializer, ProductImageSerializer, OrderSerializer

logger = logging.getLogger(__name__)


class ProductViewSet(viewsets.ModelViewSet):
    """CRUD for products. Admin-only for write ops, public for read."""
    serializer_class = ProductSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        qs = Product.objects.filter(tenant=tenant).prefetch_related('images')
        if self.request.method == 'GET' and not self.request.user.is_authenticated:
            qs = qs.filter(active=True)
        return qs

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        if self.action == 'destroy':
            return [IsManagerOrAbove()]
        return [IsAuthenticated()]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        serializer.save(tenant=tenant)

    def perform_update(self, serializer):
        serializer.save()


class OrderViewSet(viewsets.ModelViewSet):
    """Orders — admin can list/update, public can create via checkout."""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        return Order.objects.filter(tenant=tenant).prefetch_related('items')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_product_images(request, product_id):
    """Upload one or more images to a product. Accepts multipart form with 'images' field."""
    tenant = getattr(request, 'tenant', None)
    try:
        product = Product.objects.get(id=product_id, tenant=tenant)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=404)

    files = request.FILES.getlist('images')
    if not files:
        return Response({'error': 'No images provided'}, status=400)

    max_order = ProductImage.objects.filter(product=product).count()
    created = []
    for i, f in enumerate(files):
        img = ProductImage.objects.create(
            product=product,
            image=f,
            alt_text=f.name,
            sort_order=max_order + i,
        )
        created.append(img)

    serializer = ProductImageSerializer(created, many=True, context={'request': request})
    return Response(serializer.data, status=201)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_product_image(request, product_id, image_id):
    """Delete a single image from a product."""
    tenant = getattr(request, 'tenant', None)
    try:
        img = ProductImage.objects.get(id=image_id, product_id=product_id, product__tenant=tenant)
    except ProductImage.DoesNotExist:
        return Response({'error': 'Image not found'}, status=404)
    img.image.delete(save=False)
    img.delete()
    return Response(status=204)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reorder_product_images(request, product_id):
    """Reorder images for a product. Expects JSON: { "order": [image_id, image_id, ...] }"""
    tenant = getattr(request, 'tenant', None)
    try:
        Product.objects.get(id=product_id, tenant=tenant)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=404)

    order = request.data.get('order', [])
    for idx, img_id in enumerate(order):
        ProductImage.objects.filter(id=img_id, product_id=product_id).update(sort_order=idx)
    return Response({'status': 'ok'})


@api_view(['POST'])
@permission_classes([AllowAny])
def create_shop_checkout(request):
    """Create a Stripe checkout session for a product order."""
    import stripe
    from django.conf import settings

    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=400)

    items = request.data.get('items', [])
    customer_name = request.data.get('customer_name', '')
    customer_email = request.data.get('customer_email', '')
    customer_phone = request.data.get('customer_phone', '')

    if not items or not customer_email:
        return Response({'error': 'Items and customer_email are required'}, status=400)

    line_items = []
    order_items = []
    total_pence = 0

    for item in items:
        product_id = item.get('product_id')
        quantity = int(item.get('quantity', 1))

        if quantity <= 0:
            return Response({'error': f'Quantity must be at least 1 (got {quantity})'}, status=400)

        try:
            product = Product.objects.get(id=product_id, tenant=tenant, active=True)
        except Product.DoesNotExist:
            return Response({'error': f'Product {product_id} not found'}, status=400)

        if product.track_stock and product.stock_quantity < quantity:
            return Response({'error': f'{product.name} — only {product.stock_quantity} in stock'}, status=400)

        line_items.append({
            'price_data': {
                'currency': getattr(tenant, 'currency', 'GBP').lower(),
                'product_data': {'name': product.name},
                'unit_amount': product.price_pence,
            },
            'quantity': quantity,
        })
        order_items.append({
            'product': product,
            'product_name': product.name,
            'quantity': quantity,
            'unit_price_pence': product.price_pence,
        })
        total_pence += product.price_pence * quantity

    order = Order.objects.create(
        tenant=tenant,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
        total_pence=total_pence,
        status='pending',
    )
    for oi in order_items:
        OrderItem.objects.create(order=order, **oi)

    # Deduct stock
    for item in items:
        product = Product.objects.get(id=item['product_id'])
        if product.track_stock:
            product.stock_quantity = max(0, product.stock_quantity - int(item.get('quantity', 1)))
            product.save(update_fields=['stock_quantity'])

    stripe_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
    if not stripe_key:
        order.status = 'paid'
        order.save(update_fields=['status'])
        return Response({
            'order_id': order.id,
            'status': 'paid',
            'message': 'Order created (Stripe not configured — marked as paid)',
        })

    stripe.api_key = stripe_key
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            customer_email=customer_email,
            success_url=f'{frontend_url}/shop/success?order={order.id}',
            cancel_url=f'{frontend_url}/shop?cancelled=true',
            metadata={'order_id': str(order.id), 'tenant_slug': tenant.slug},
        )
        order.stripe_session_id = session.id
        order.save(update_fields=['stripe_session_id'])
        return Response({'checkout_url': session.url, 'order_id': order.id})
    except Exception as e:
        logger.exception('Stripe checkout error')
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_products(request):
    """Public endpoint — list active products for the shop page."""
    tenant = getattr(request, 'tenant', None)
    products = Product.objects.filter(tenant=tenant, active=True).prefetch_related('images')
    category = request.query_params.get('category')
    if category:
        products = products.filter(category__iexact=category)
    serializer = ProductSerializer(products, many=True, context={'request': request})
    return Response(serializer.data)

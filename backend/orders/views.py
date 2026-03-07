import random
import string
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import (
    MenuCategory, MenuItem, Order, OrderItem,
    OrderQueueSettings, DailyOrderSummary, ItemDailySales,
)
from .serializers import (
    MenuCategorySerializer, MenuCategoryListSerializer, MenuItemSerializer,
    OrderSerializer, OrderCreateSerializer, OrderQueueSettingsSerializer,
    DailyOrderSummarySerializer, ItemDailySalesSerializer,
)


def _generate_order_ref():
    """Generate a short, human-readable order reference like 'A7K3'."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))


# =============================================================================
# Public endpoints (no auth required) — customer-facing
# =============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def public_menu(request):
    """Return the full menu with categories and items for the customer order page."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=404)

    categories = MenuCategory.objects.filter(
        tenant=tenant, active=True
    ).prefetch_related('items')

    # Filter to only active, non-sold-out items within each category
    data = []
    for cat in categories:
        cat_data = MenuCategorySerializer(cat).data
        cat_data['items'] = [
            item for item in cat_data['items']
            if item['active']
        ]
        if cat_data['items']:  # Only include categories with items
            data.append(cat_data)

    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_queue_status(request):
    """Return current wait time and whether orders are being accepted."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=404)

    settings, _ = OrderQueueSettings.objects.get_or_create(tenant=tenant)
    return Response(OrderQueueSettingsSerializer(settings).data)


@api_view(['POST'])
@permission_classes([AllowAny])
def place_order(request):
    """Place a new order from the customer-facing page."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=404)

    # Check if accepting orders
    queue_settings, _ = OrderQueueSettings.objects.get_or_create(tenant=tenant)
    if not queue_settings.accepting_orders:
        msg = queue_settings.not_accepting_reason or 'We are not currently accepting orders.'
        return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)
    if queue_settings.seasonal_closed:
        msg = queue_settings.seasonal_message or 'We are closed for the season.'
        return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

    serializer = OrderCreateSerializer(data=request.data)
    if not serializer.is_valid():
        # Flatten DRF validation errors into a readable string
        errors = serializer.errors
        parts = []
        for field, msgs in errors.items():
            if isinstance(msgs, list):
                parts.append(f"{field}: {', '.join(str(m) for m in msgs)}")
            else:
                parts.append(f"{field}: {msgs}")
        return Response({'error': '; '.join(parts) or 'Validation error', 'detail': errors}, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    items_data = data['items']

    # Validate menu items exist and are available
    order_items = []
    for item_data in items_data:
        menu_item_id = item_data.get('menu_item_id')
        quantity = int(item_data.get('quantity', 1))
        notes = item_data.get('notes', '')
        try:
            menu_item = MenuItem.objects.get(
                id=menu_item_id, tenant=tenant, active=True
            )
        except MenuItem.DoesNotExist:
            return Response(
                {'error': f'Menu item {menu_item_id} not found or unavailable'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if menu_item.sold_out:
            return Response(
                {'error': f'"{menu_item.name}" is currently sold out'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order_items.append({
            'menu_item': menu_item,
            'quantity': quantity,
            'notes': notes,
        })

    # Generate unique order ref
    for _ in range(10):
        ref = _generate_order_ref()
        if not Order.objects.filter(tenant=tenant, order_ref=ref).exists():
            break

    # Calculate wait time
    wait_minutes = queue_settings.calculate_wait_time()

    # Create order
    order = Order.objects.create(
        tenant=tenant,
        order_ref=ref,
        customer_name=data['customer_name'],
        customer_phone=data.get('customer_phone', ''),
        customer_email=data.get('customer_email', ''),
        source=data.get('source', 'online'),
        payment_method=data.get('payment_method', 'cash'),
        notes=data.get('notes', ''),
        estimated_ready_minutes=wait_minutes,
        estimated_ready_at=timezone.now() + timezone.timedelta(minutes=wait_minutes),
    )

    # Create order items
    for oi in order_items:
        OrderItem.objects.create(
            order=order,
            menu_item=oi['menu_item'],
            name=oi['menu_item'].name,
            quantity=oi['quantity'],
            unit_price_pence=oi['menu_item'].price_pence,
            notes=oi['notes'],
        )

    # Calculate totals
    order.calculate_totals()
    order.save()

    # Stripe checkout for card payments
    if order.payment_method == 'card':
        from django.conf import settings as django_settings
        stripe_key = getattr(django_settings, 'STRIPE_SECRET_KEY', '')
        if stripe_key:
            try:
                import stripe as stripe_lib
                stripe_lib.api_key = stripe_key
                origin = request.META.get('HTTP_ORIGIN') or request.META.get('HTTP_REFERER', '')
                if origin:
                    from urllib.parse import urlparse
                    parsed = urlparse(origin)
                    frontend_url = f'{parsed.scheme}://{parsed.netloc}'
                else:
                    frontend_url = getattr(django_settings, 'FRONTEND_URL', 'http://localhost:3000')

                checkout_session = stripe_lib.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': 'gbp',
                            'product_data': {
                                'name': f'Order #{order.order_ref}',
                                'description': ', '.join(
                                    f'{oi["quantity"]}x {oi["menu_item"].name}' for oi in order_items
                                ),
                            },
                            'unit_amount': order.total_pence,
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    customer_email=order.customer_email or None,
                    success_url=f'{frontend_url}/order?payment=success&order_ref={order.order_ref}',
                    cancel_url=f'{frontend_url}/order?payment=cancelled&order_ref={order.order_ref}',
                    metadata={'order_id': str(order.id), 'order_ref': order.order_ref},
                )
                response_data = OrderSerializer(order).data
                response_data['checkout_url'] = checkout_session.url
                return Response(response_data, status=status.HTTP_201_CREATED)
            except Exception:
                pass  # Stripe failed — fall through to normal response

    return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def order_status(request, order_ref):
    """Public endpoint for customer to check their order status."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=404)

    try:
        order = Order.objects.get(tenant=tenant, order_ref=order_ref.upper())
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=404)

    return Response(OrderSerializer(order).data)


# =============================================================================
# Kitchen display endpoints (authenticated — staff/owner)
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def kitchen_queue(request):
    """Live order queue for kitchen display. Returns active orders."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=404)

    status_filter = request.query_params.get('status', '')
    qs = Order.objects.filter(tenant=tenant).prefetch_related('items__menu_item')

    if status_filter:
        statuses = [s.strip() for s in status_filter.split(',')]
        qs = qs.filter(status__in=statuses)
    else:
        # Default: show active orders (received + preparing)
        qs = qs.filter(status__in=['received', 'preparing'])

    # Order by: preparing first, then received, oldest first within each
    qs = qs.order_by(
        models_status_order(),
        'placed_at',
    )

    return Response(OrderSerializer(qs[:50], many=True).data)


def models_status_order():
    """Custom ordering: preparing first, then received."""
    from django.db.models import Case, When, IntegerField
    return Case(
        When(status='preparing', then=0),
        When(status='received', then=1),
        When(status='ready', then=2),
        default=3,
        output_field=IntegerField(),
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_order_status(request, pk):
    """Move an order to a new status."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=404)

    try:
        order = Order.objects.get(id=pk, tenant=tenant)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=404)

    new_status = request.data.get('status')
    valid_statuses = ['received', 'preparing', 'ready', 'collected', 'cancelled']
    if new_status not in valid_statuses:
        return Response({'error': f'Invalid status. Must be one of: {valid_statuses}'}, status=400)

    order.transition_status(new_status)
    return Response(OrderSerializer(order).data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_order_notes(request, pk):
    """Update kitchen notes on an order."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=404)

    try:
        order = Order.objects.get(id=pk, tenant=tenant)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=404)

    if 'kitchen_notes' in request.data:
        order.kitchen_notes = request.data['kitchen_notes']
    if 'payment_confirmed' in request.data:
        order.payment_confirmed = request.data['payment_confirmed']
    if 'payment_method' in request.data:
        order.payment_method = request.data['payment_method']
    order.save()
    return Response(OrderSerializer(order).data)


# =============================================================================
# Admin — Menu management
# =============================================================================

class MenuCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = MenuCategoryListSerializer

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        qs = MenuCategory.objects.filter(tenant=tenant) if tenant else MenuCategory.objects.none()
        if self.action == 'list' and not self.request.query_params.get('all'):
            return qs.filter(active=True)
        return qs

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MenuCategorySerializer
        return MenuCategoryListSerializer

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        serializer.save(tenant=tenant)


class MenuItemViewSet(viewsets.ModelViewSet):
    serializer_class = MenuItemSerializer

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        qs = MenuItem.objects.filter(tenant=tenant) if tenant else MenuItem.objects.none()
        category_id = self.request.query_params.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)
        if self.action == 'list' and not self.request.query_params.get('all'):
            return qs.filter(active=True)
        return qs

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        serializer.save(tenant=tenant)

    @action(detail=True, methods=['post'])
    def toggle_sold_out(self, request, pk=None):
        """Toggle sold-out status for a menu item."""
        item = self.get_object()
        item.sold_out = not item.sold_out
        item.save()
        return Response(MenuItemSerializer(item).data)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def queue_settings(request):
    """Get or update order queue settings."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=404)

    settings_obj, _ = OrderQueueSettings.objects.get_or_create(tenant=tenant)

    if request.method == 'PATCH':
        serializer = OrderQueueSettingsSerializer(settings_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    return Response(OrderQueueSettingsSerializer(settings_obj).data)


# =============================================================================
# Admin — Order history and analytics
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_history(request):
    """Paginated order history with filters."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=404)

    qs = Order.objects.filter(tenant=tenant).prefetch_related('items__menu_item')

    # Filters
    status_filter = request.query_params.get('status')
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    source = request.query_params.get('source')
    search = request.query_params.get('search')

    if status_filter:
        qs = qs.filter(status=status_filter)
    if date_from:
        qs = qs.filter(placed_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(placed_at__date__lte=date_to)
    if source:
        qs = qs.filter(source=source)
    if search:
        from django.db.models import Q
        qs = qs.filter(
            Q(customer_name__icontains=search) |
            Q(order_ref__icontains=search) |
            Q(customer_phone__icontains=search)
        )

    # Pagination
    limit = min(int(request.query_params.get('limit', 50)), 200)
    offset = int(request.query_params.get('offset', 0))
    total = qs.count()
    orders = qs[offset:offset + limit]

    return Response({
        'results': OrderSerializer(orders, many=True).data,
        'total': total,
        'limit': limit,
        'offset': offset,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_summary(request):
    """Return daily order summaries for analytics."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=404)

    days = int(request.query_params.get('days', 30))
    from_date = timezone.now().date() - timezone.timedelta(days=days)

    summaries = DailyOrderSummary.objects.filter(
        tenant=tenant, date__gte=from_date,
    )
    return Response(DailyOrderSummarySerializer(summaries, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def item_sales(request):
    """Return per-item sales data for analytics and procurement."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=404)

    days = int(request.query_params.get('days', 30))
    menu_item_id = request.query_params.get('menu_item')
    from_date = timezone.now().date() - timezone.timedelta(days=days)

    qs = ItemDailySales.objects.filter(tenant=tenant, date__gte=from_date)
    if menu_item_id:
        qs = qs.filter(menu_item_id=menu_item_id)

    return Response(ItemDailySalesSerializer(qs, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def today_dashboard(request):
    """Quick dashboard: today's stats + active orders count."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=404)

    today = timezone.now().date()
    today_orders = Order.objects.filter(tenant=tenant, placed_at__date=today)

    active = today_orders.filter(status__in=['received', 'preparing']).count()
    completed = today_orders.filter(status='collected').count()
    cancelled = today_orders.filter(status='cancelled').count()
    ready = today_orders.filter(status='ready').count()
    total_revenue = sum(o.total_pence for o in today_orders.filter(status='collected'))

    # Queue settings
    queue_settings_obj, _ = OrderQueueSettings.objects.get_or_create(tenant=tenant)

    return Response({
        'date': str(today),
        'active_orders': active,
        'ready_orders': ready,
        'completed_orders': completed,
        'cancelled_orders': cancelled,
        'total_orders': today_orders.count(),
        'total_revenue_pence': total_revenue,
        'total_revenue_display': f"£{total_revenue / 100:.2f}",
        'current_wait_minutes': queue_settings_obj.calculate_wait_time(),
        'accepting_orders': queue_settings_obj.accepting_orders,
    })

"""Analytics and procurement prediction API views."""

import datetime
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .analytics import (
    predict_demand, predict_week, procurement_report,
    aggregate_daily_summary, get_uk_bank_holidays, get_uk_school_holidays,
    is_school_holiday, is_bank_holiday,
)
from .models import Order, DailyOrderSummary, ItemDailySales, MenuItem


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def demand_prediction(request):
    """
    Predict demand for a specific date.
    Query params: ?date=YYYY-MM-DD (defaults to tomorrow)
    """
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=404)

    date_str = request.query_params.get('date')
    if date_str:
        try:
            target_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
    else:
        target_date = timezone.now().date() + datetime.timedelta(days=1)

    result = predict_demand(tenant, target_date)
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def week_prediction(request):
    """
    Predict demand for the next 7 days.
    Query params: ?start=YYYY-MM-DD (defaults to tomorrow)
    """
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=404)

    date_str = request.query_params.get('start')
    if date_str:
        try:
            start_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
    else:
        start_date = timezone.now().date() + datetime.timedelta(days=1)

    result = predict_week(tenant, start_date)
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def procurement_forecast(request):
    """
    Generate a procurement shopping list for the next N days.
    Query params: ?start=YYYY-MM-DD&days=7
    """
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=404)

    date_str = request.query_params.get('start')
    if date_str:
        try:
            start_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
    else:
        start_date = timezone.now().date() + datetime.timedelta(days=1)

    days = min(int(request.query_params.get('days', 7)), 30)
    result = procurement_report(tenant, start_date, days)
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def holiday_calendar(request):
    """
    Return UK bank holidays and school holiday periods for a year.
    Query params: ?year=2026
    """
    year = int(request.query_params.get('year', timezone.now().year))

    bank_holidays = get_uk_bank_holidays(year)
    school_holidays = get_uk_school_holidays(year)

    return Response({
        'year': year,
        'bank_holidays': [
            {'date': str(d), 'name': n}
            for d, n in sorted(bank_holidays.items())
        ],
        'school_holidays': [
            {'start': str(s), 'end': str(e), 'name': n}
            for s, e, n in school_holidays
        ],
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rebuild_summaries(request):
    """
    Rebuild daily summaries for a date range.
    Body: {from_date: "YYYY-MM-DD", to_date: "YYYY-MM-DD"}
    """
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=404)

    from_str = request.data.get('from_date')
    to_str = request.data.get('to_date')

    if not from_str or not to_str:
        return Response({'error': 'from_date and to_date required'}, status=400)

    try:
        from_date = datetime.date.fromisoformat(from_str)
        to_date = datetime.date.fromisoformat(to_str)
    except ValueError:
        return Response({'error': 'Invalid date format'}, status=400)

    if (to_date - from_date).days > 365:
        return Response({'error': 'Max 365 days'}, status=400)

    count = 0
    current = from_date
    while current <= to_date:
        aggregate_daily_summary(tenant, current)
        count += 1
        current += datetime.timedelta(days=1)

    return Response({'rebuilt': count, 'from': str(from_date), 'to': str(to_date)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_trends(request):
    """
    Return sales trends: compare current period vs previous period.
    Query params: ?days=7 (compare last 7 days vs previous 7 days)
    """
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=404)

    days = int(request.query_params.get('days', 7))
    today = timezone.now().date()

    current_start = today - datetime.timedelta(days=days)
    previous_start = current_start - datetime.timedelta(days=days)

    current = DailyOrderSummary.objects.filter(
        tenant=tenant, date__gte=current_start, date__lt=today,
    ).aggregate(
        orders=Sum('total_orders'),
        revenue=Sum('total_revenue_pence'),
        items=Sum('total_items_sold'),
    )

    previous = DailyOrderSummary.objects.filter(
        tenant=tenant, date__gte=previous_start, date__lt=current_start,
    ).aggregate(
        orders=Sum('total_orders'),
        revenue=Sum('total_revenue_pence'),
        items=Sum('total_items_sold'),
    )

    def pct_change(current_val, prev_val):
        c = current_val or 0
        p = prev_val or 0
        if p == 0:
            return 100.0 if c > 0 else 0.0
        return round(((c - p) / p) * 100, 1)

    return Response({
        'period_days': days,
        'current': {
            'start': str(current_start),
            'end': str(today),
            'total_orders': current['orders'] or 0,
            'total_revenue_pence': current['revenue'] or 0,
            'total_items': current['items'] or 0,
        },
        'previous': {
            'start': str(previous_start),
            'end': str(current_start),
            'total_orders': previous['orders'] or 0,
            'total_revenue_pence': previous['revenue'] or 0,
            'total_items': previous['items'] or 0,
        },
        'change': {
            'orders_pct': pct_change(current['orders'], previous['orders']),
            'revenue_pct': pct_change(current['revenue'], previous['revenue']),
            'items_pct': pct_change(current['items'], previous['items']),
        },
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def popular_items(request):
    """Top-selling items for a period."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=404)

    days = int(request.query_params.get('days', 30))
    from_date = timezone.now().date() - datetime.timedelta(days=days)
    limit = min(int(request.query_params.get('limit', 10)), 50)

    items = ItemDailySales.objects.filter(
        tenant=tenant, date__gte=from_date,
    ).values('menu_item', 'menu_item__name').annotate(
        total_qty=Sum('quantity_sold'),
        total_revenue=Sum('revenue_pence'),
    ).order_by('-total_qty')[:limit]

    return Response({
        'period_days': days,
        'items': list(items),
    })

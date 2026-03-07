"""
Smart Analytics & Procurement Prediction Engine for Orders Module.

Key features:
- Recognises UK school holidays, bank holidays, Easter (date-variable)
- Seasonal demand patterns (tourist locations: dead Nov-Mar, peak Jul-Aug)
- Day-of-week patterns
- Weather correlation (optional)
- Per-item procurement forecasting
"""

import datetime
from collections import defaultdict
from django.utils import timezone
from django.db.models import Sum, Avg, Count, F, Q

from .models import Order, OrderItem, MenuItem, DailyOrderSummary, ItemDailySales


# =============================================================================
# UK Holiday Calendar — date-aware, handles moving dates
# =============================================================================

def _easter_date(year):
    """Calculate Easter Sunday using the Anonymous Gregorian algorithm."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return datetime.date(year, month, day)


def get_uk_bank_holidays(year):
    """Return dict of {date: name} for UK (England) bank holidays in given year."""
    holidays = {}

    # New Year's Day (or substitute)
    nyd = datetime.date(year, 1, 1)
    if nyd.weekday() == 5:  # Saturday
        holidays[datetime.date(year, 1, 3)] = "New Year's Day (substitute)"
    elif nyd.weekday() == 6:  # Sunday
        holidays[datetime.date(year, 1, 2)] = "New Year's Day (substitute)"
    else:
        holidays[nyd] = "New Year's Day"

    # Easter
    easter = _easter_date(year)
    holidays[easter - datetime.timedelta(days=2)] = 'Good Friday'
    holidays[easter + datetime.timedelta(days=1)] = 'Easter Monday'

    # Early May bank holiday (first Monday in May)
    may1 = datetime.date(year, 5, 1)
    may_bh = may1 + datetime.timedelta(days=(7 - may1.weekday()) % 7)
    holidays[may_bh] = 'Early May Bank Holiday'

    # Spring bank holiday (last Monday in May)
    may31 = datetime.date(year, 5, 31)
    spring_bh = may31 - datetime.timedelta(days=(may31.weekday()))
    if spring_bh.weekday() != 0:
        spring_bh = may31 - datetime.timedelta(days=may31.weekday())
    holidays[spring_bh] = 'Spring Bank Holiday'

    # Summer bank holiday (last Monday in August)
    aug31 = datetime.date(year, 8, 31)
    summer_bh = aug31 - datetime.timedelta(days=aug31.weekday())
    holidays[summer_bh] = 'Summer Bank Holiday'

    # Christmas Day (or substitute)
    xmas = datetime.date(year, 12, 25)
    boxing = datetime.date(year, 12, 26)
    if xmas.weekday() == 5:  # Saturday
        holidays[datetime.date(year, 12, 27)] = 'Christmas Day (substitute)'
        holidays[datetime.date(year, 12, 28)] = 'Boxing Day (substitute)'
    elif xmas.weekday() == 6:  # Sunday
        holidays[datetime.date(year, 12, 27)] = 'Boxing Day (substitute)'
        holidays[datetime.date(year, 12, 26)] = 'Boxing Day'
        holidays[datetime.date(year, 12, 25)] = 'Christmas Day'
    else:
        holidays[xmas] = 'Christmas Day'
        if boxing.weekday() == 6:  # Sunday
            holidays[datetime.date(year, 12, 28)] = 'Boxing Day (substitute)'
        else:
            holidays[boxing] = 'Boxing Day'

    return holidays


def get_uk_school_holidays(year):
    """
    Return approximate UK school holiday periods for a given year.
    These are estimates — actual dates vary by local authority.
    Returns list of (start_date, end_date, name) tuples.

    Key insight: Easter moves (March/April), half-terms shift,
    and summer dates are fairly stable.
    """
    easter = _easter_date(year)

    periods = [
        # Christmas holidays (straddles years)
        (datetime.date(year, 1, 1), datetime.date(year, 1, 5), 'Christmas Holidays'),
        # February half-term (week containing 3rd Monday of Feb, roughly)
        (datetime.date(year, 2, 10), datetime.date(year, 2, 16), 'February Half-Term'),
        # Easter holidays (2 weeks around Easter — varies year to year!)
        (easter - datetime.timedelta(days=9), easter + datetime.timedelta(days=7), 'Easter Holidays'),
        # May half-term (last week of May / first of June)
        (datetime.date(year, 5, 24), datetime.date(year, 6, 1), 'May Half-Term'),
        # Summer holidays (late July to early September)
        (datetime.date(year, 7, 20), datetime.date(year, 9, 3), 'Summer Holidays'),
        # October half-term
        (datetime.date(year, 10, 21), datetime.date(year, 10, 27), 'October Half-Term'),
        # Christmas holidays (end of year)
        (datetime.date(year, 12, 20), datetime.date(year, 12, 31), 'Christmas Holidays'),
    ]
    return periods


def is_school_holiday(date):
    """Check if a date falls within an approximate UK school holiday period."""
    periods = get_uk_school_holidays(date.year)
    for start, end, name in periods:
        if start <= date <= end:
            return True, name
    return False, ''


def is_bank_holiday(date):
    """Check if a date is a UK bank holiday."""
    holidays = get_uk_bank_holidays(date.year)
    if date in holidays:
        return True, holidays[date]
    return False, ''


# =============================================================================
# Daily Summary Aggregation
# =============================================================================

def aggregate_daily_summary(tenant, date):
    """Build or update DailyOrderSummary for a specific date."""
    orders = Order.objects.filter(
        tenant=tenant,
        placed_at__date=date,
    ).exclude(status='cancelled')

    cancelled = Order.objects.filter(
        tenant=tenant,
        placed_at__date=date,
        status='cancelled',
    ).count()

    total_orders = orders.count()
    total_revenue = orders.aggregate(s=Sum('total_pence'))['s'] or 0
    total_items = OrderItem.objects.filter(
        order__in=orders,
    ).aggregate(s=Sum('quantity'))['s'] or 0
    avg_value = total_revenue // total_orders if total_orders > 0 else 0

    # Calculate average wait time (placed → collected)
    collected = orders.filter(collected_at__isnull=False)
    if collected.exists():
        from django.db.models import Avg as DjAvg, ExpressionWrapper, DurationField
        avg_wait = 0
        wait_count = 0
        for o in collected:
            if o.collected_at and o.placed_at:
                delta = (o.collected_at - o.placed_at).total_seconds() / 60
                avg_wait += delta
                wait_count += 1
        avg_wait = avg_wait / wait_count if wait_count > 0 else 0
    else:
        avg_wait = 0

    # Peak hour
    from django.db.models.functions import ExtractHour
    peak = orders.annotate(
        hour=ExtractHour('placed_at')
    ).values('hour').annotate(
        cnt=Count('id')
    ).order_by('-cnt').first()
    peak_hour = peak['hour'] if peak else None

    # Holiday flags
    school_hol, school_name = is_school_holiday(date)
    bank_hol, bank_name = is_bank_holiday(date)

    summary, _ = DailyOrderSummary.objects.update_or_create(
        tenant=tenant,
        date=date,
        defaults={
            'total_orders': total_orders,
            'total_revenue_pence': total_revenue,
            'total_items_sold': total_items,
            'avg_order_value_pence': avg_value,
            'peak_hour': peak_hour,
            'cancelled_orders': cancelled,
            'avg_wait_minutes': avg_wait,
            'is_school_holiday': school_hol,
            'is_bank_holiday': bank_hol,
            'is_weekend': date.weekday() >= 5,
            'holiday_name': bank_name or school_name,
            'day_of_week': date.weekday(),
            'week_number': date.isocalendar()[1],
        },
    )

    # Per-item breakdown
    item_totals = OrderItem.objects.filter(
        order__in=orders,
    ).values('menu_item').annotate(
        qty=Sum('quantity'),
        rev=Sum(F('quantity') * F('unit_price_pence')),
    )
    for it in item_totals:
        ItemDailySales.objects.update_or_create(
            tenant=tenant,
            menu_item_id=it['menu_item'],
            date=date,
            defaults={
                'quantity_sold': it['qty'],
                'revenue_pence': it['rev'],
                'is_school_holiday': school_hol,
                'is_bank_holiday': bank_hol,
                'is_weekend': date.weekday() >= 5,
                'day_of_week': date.weekday(),
                'week_number': date.isocalendar()[1],
            },
        )

    return summary


# =============================================================================
# Procurement Prediction Engine
# =============================================================================

def predict_demand(tenant, target_date, days_history=365):
    """
    Predict demand for each menu item on a target date.

    Strategy:
    1. Find "similar" historical days (same day-of-week, same holiday context)
    2. Weight recent data more heavily
    3. Apply seasonal multiplier
    4. Return per-item predicted quantities + confidence

    The key insight: school holidays, Easter, bank holidays don't fall on the
    same calendar dates each year, so we match on CONTEXT not calendar date.
    """
    from_date = target_date - datetime.timedelta(days=days_history)

    # Determine target date context
    target_dow = target_date.weekday()
    target_school_hol, _ = is_school_holiday(target_date)
    target_bank_hol, _ = is_bank_holiday(target_date)
    target_month = target_date.month
    target_is_weekend = target_dow >= 5

    # Get all historical daily summaries
    history = DailyOrderSummary.objects.filter(
        tenant=tenant,
        date__gte=from_date,
        date__lt=target_date,
    )

    if not history.exists():
        return {
            'target_date': str(target_date),
            'confidence': 0,
            'message': 'No historical data available',
            'predicted_total_orders': 0,
            'items': [],
        }

    # Score each historical day by similarity to target
    scored_days = []
    for day in history:
        score = 0.0
        weight = 1.0

        # Same day of week: strong signal
        if day.day_of_week == target_dow:
            score += 3.0

        # Same holiday context: very strong signal
        if day.is_school_holiday == target_school_hol:
            score += 4.0
        if day.is_bank_holiday == target_bank_hol:
            score += 2.0
        if day.is_weekend == target_is_weekend:
            score += 1.0

        # Same month/season: moderate signal
        if day.date.month == target_month:
            score += 2.0
        elif abs(day.date.month - target_month) <= 1 or abs(day.date.month - target_month) >= 11:
            score += 1.0

        # Recency weighting: more recent = more relevant
        days_ago = (target_date - day.date).days
        if days_ago <= 30:
            weight = 2.0
        elif days_ago <= 90:
            weight = 1.5
        elif days_ago <= 180:
            weight = 1.0
        else:
            weight = 0.5

        final_score = score * weight
        if final_score > 0:
            scored_days.append((day, final_score))

    if not scored_days:
        return {
            'target_date': str(target_date),
            'confidence': 0,
            'message': 'No similar historical days found',
            'predicted_total_orders': 0,
            'items': [],
        }

    # Sort by score descending, take top N similar days
    scored_days.sort(key=lambda x: -x[1])
    top_days = scored_days[:min(20, len(scored_days))]
    top_dates = [d.date for d, _ in top_days]
    top_weights = {d.date: w for d, w in top_days}

    # Weighted average of total orders
    total_weight = sum(w for _, w in top_days)
    predicted_orders = sum(
        d.total_orders * w for d, w in top_days
    ) / total_weight if total_weight > 0 else 0

    predicted_revenue = sum(
        d.total_revenue_pence * w for d, w in top_days
    ) / total_weight if total_weight > 0 else 0

    # Per-item prediction from ItemDailySales
    item_sales = ItemDailySales.objects.filter(
        tenant=tenant,
        date__in=top_dates,
    ).values('menu_item', 'menu_item__name').annotate(
        total_qty=Sum('quantity_sold'),
        count_days=Count('date', distinct=True),
    )

    item_predictions = []
    for item in item_sales:
        # Weighted average per item
        item_daily = ItemDailySales.objects.filter(
            tenant=tenant,
            menu_item_id=item['menu_item'],
            date__in=top_dates,
        )
        weighted_qty = sum(
            ids.quantity_sold * top_weights.get(ids.date, 1.0)
            for ids in item_daily
        )
        weighted_total = sum(
            top_weights.get(ids.date, 1.0)
            for ids in item_daily
        )
        predicted_qty = weighted_qty / weighted_total if weighted_total > 0 else 0

        item_predictions.append({
            'menu_item_id': item['menu_item'],
            'name': item['menu_item__name'],
            'predicted_quantity': round(predicted_qty, 1),
            'predicted_quantity_rounded': max(1, round(predicted_qty)),
            'historical_days_matched': item['count_days'],
            'total_historical_sold': item['total_qty'],
        })

    # Sort by predicted quantity descending
    item_predictions.sort(key=lambda x: -x['predicted_quantity'])

    # Confidence score (0-100)
    confidence = min(100, len(top_days) * 5)  # 20 similar days = 100% confidence

    return {
        'target_date': str(target_date),
        'target_context': {
            'day_of_week': target_dow,
            'day_name': target_date.strftime('%A'),
            'is_school_holiday': target_school_hol,
            'is_bank_holiday': target_bank_hol,
            'is_weekend': target_is_weekend,
            'month': target_month,
        },
        'confidence': confidence,
        'similar_days_used': len(top_days),
        'predicted_total_orders': round(predicted_orders, 1),
        'predicted_revenue_pence': round(predicted_revenue),
        'predicted_revenue_display': f"£{predicted_revenue / 100:.2f}",
        'items': item_predictions,
    }


def predict_week(tenant, start_date):
    """Predict demand for 7 days starting from start_date."""
    predictions = []
    for i in range(7):
        date = start_date + datetime.timedelta(days=i)
        pred = predict_demand(tenant, date)
        predictions.append(pred)
    return predictions


def procurement_report(tenant, start_date, days=7):
    """
    Generate a procurement shopping list for the next N days.
    Aggregates per-item predictions into total quantities needed.
    """
    item_totals = defaultdict(lambda: {
        'name': '',
        'total_predicted': 0,
        'daily_breakdown': [],
        'menu_item_id': None,
    })

    for i in range(days):
        date = start_date + datetime.timedelta(days=i)
        pred = predict_demand(tenant, date)
        for item in pred.get('items', []):
            mid = item['menu_item_id']
            item_totals[mid]['name'] = item['name']
            item_totals[mid]['menu_item_id'] = mid
            item_totals[mid]['total_predicted'] += item['predicted_quantity_rounded']
            item_totals[mid]['daily_breakdown'].append({
                'date': str(date),
                'day': date.strftime('%A'),
                'quantity': item['predicted_quantity_rounded'],
            })

    # Convert to sorted list
    result = sorted(
        item_totals.values(),
        key=lambda x: -x['total_predicted'],
    )

    return {
        'period_start': str(start_date),
        'period_end': str(start_date + datetime.timedelta(days=days - 1)),
        'days': days,
        'items': result,
    }

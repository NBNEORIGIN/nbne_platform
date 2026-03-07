"""
Seed demo data for Pizza Shack X — the cafe/takeaway demo tenant.

Creates:
- Tenant settings (pizza-shack-x)
- Menu categories and items
- Historical orders spanning 12 months with realistic seasonal patterns
- Daily summaries for analytics/procurement prediction

Idempotent: safe to run multiple times.
"""

import random
import string
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from tenants.models import TenantSettings
from accounts.models import User
from orders.models import (
    MenuCategory, MenuItem, Order, OrderItem,
    OrderQueueSettings, DailyOrderSummary, ItemDailySales,
)
from orders.analytics import (
    aggregate_daily_summary, is_school_holiday, is_bank_holiday,
)


# Pizza Shack menu
MENU = {
    'Pizzas': {
        'icon': '🍕',
        'items': [
            ('Margherita', 'Classic tomato, mozzarella, fresh basil', 850, 12, False, False, False),
            ('Pepperoni', 'Spicy pepperoni, mozzarella, tomato sauce', 950, 12, False, False, False),
            ('Hawaiian', 'Ham, pineapple, mozzarella', 950, 12, False, False, False),
            ('Veggie Supreme', 'Peppers, mushrooms, onions, olives, sweetcorn', 950, 14, True, False, False),
            ('BBQ Chicken', 'BBQ sauce, chicken, red onion, mozzarella', 1050, 14, False, False, False),
            ('Meat Feast', 'Pepperoni, ham, bacon, sausage', 1150, 14, False, False, False),
            ('Quattro Formaggi', 'Mozzarella, cheddar, parmesan, blue cheese', 1050, 14, True, False, False),
            ('Spicy Nduja', 'Nduja sausage, chilli flakes, rocket, mozzarella', 1150, 14, False, False, False),
        ],
    },
    'Sides': {
        'icon': '🍟',
        'items': [
            ('Garlic Bread', 'Classic garlic bread with herb butter', 350, 5, True, True, False),
            ('Cheesy Garlic Bread', 'Garlic bread loaded with mozzarella', 450, 6, True, False, False),
            ('Chips', 'Crispy seasoned chips', 300, 5, True, True, True),
            ('Sweet Potato Fries', 'Crispy sweet potato fries with aioli', 400, 6, True, True, True),
            ('Coleslaw', 'Homemade creamy coleslaw', 200, 2, True, True, True),
            ('Side Salad', 'Mixed leaves, cherry tomatoes, cucumber', 250, 2, True, True, True),
        ],
    },
    'Desserts': {
        'icon': '🍰',
        'items': [
            ('Chocolate Brownie', 'Warm chocolate brownie with ice cream', 500, 5, True, False, False),
            ('Tiramisu', 'Classic Italian coffee dessert', 550, 3, True, False, False),
            ('Ice Cream (3 scoops)', 'Vanilla, chocolate, or strawberry', 350, 2, True, True, True),
            ('Cookie Dough Bites', 'Warm cookie dough bites with chocolate sauce', 450, 5, True, False, False),
        ],
    },
    'Drinks': {
        'icon': '🥤',
        'items': [
            ('Coke', 'Coca-Cola 330ml', 200, 0, True, True, True),
            ('Diet Coke', 'Diet Coca-Cola 330ml', 200, 0, True, True, True),
            ('Lemonade', 'Sparkling lemonade 330ml', 200, 0, True, True, True),
            ('Water', 'Still mineral water 500ml', 150, 0, True, True, True),
            ('Orange Juice', 'Fresh orange juice', 250, 0, True, True, True),
        ],
    },
}

FIRST_NAMES = [
    'James', 'Emma', 'Oliver', 'Olivia', 'Jack', 'Amelia', 'Harry', 'Isla',
    'George', 'Mia', 'Charlie', 'Ava', 'Thomas', 'Lily', 'Oscar', 'Emily',
    'William', 'Sophia', 'Noah', 'Grace', 'Ethan', 'Chloe', 'Lucas', 'Ella',
    'Mason', 'Freya', 'Archie', 'Poppy', 'Leo', 'Jessica', 'Henry', 'Daisy',
    'Ben', 'Sarah', 'Daniel', 'Hannah', 'Max', 'Katie', 'Sam', 'Lucy',
]

LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Wilson', 'Taylor',
    'Davies', 'Evans', 'Thomas', 'Roberts', 'Walker', 'Wright', 'Robinson',
    'Thompson', 'White', 'Hall', 'Green', 'Harris', 'Clark', 'Mitchell',
]


def _seasonal_multiplier(date):
    """
    Tourist location seasonal curve:
    - Nov-Mar: very quiet (0.1-0.3)
    - Apr, Oct: shoulder (0.5-0.7)
    - May, Jun, Sep: moderate (0.7-0.9)
    - Jul, Aug: peak (1.0-1.5)
    """
    month = date.month
    curve = {
        1: 0.1, 2: 0.15, 3: 0.2,
        4: 0.5, 5: 0.7, 6: 0.85,
        7: 1.2, 8: 1.4, 9: 0.8,
        10: 0.6, 11: 0.15, 12: 0.1,
    }
    base = curve.get(month, 0.5)

    # School holidays boost
    school_hol, _ = is_school_holiday(date)
    if school_hol:
        base *= 1.6

    # Bank holidays boost
    bank_hol, _ = is_bank_holiday(date)
    if bank_hol:
        base *= 1.4

    # Weekend boost
    if date.weekday() >= 5:
        base *= 1.3

    # Weather randomness (±20%)
    base *= random.uniform(0.8, 1.2)

    return max(0.05, base)


class Command(BaseCommand):
    help = 'Seed Pizza Shack X demo tenant with menu, orders, and analytics data'

    def add_arguments(self, parser):
        parser.add_argument('--months', type=int, default=12, help='Months of historical data')
        parser.add_argument('--clear', action='store_true', help='Clear existing demo data first')

    def handle(self, *args, **options):
        months = options['months']
        clear = options['clear']

        self.stdout.write('🍕 Seeding Pizza Shack X...')

        # 1. Create or update tenant
        tenant, created = TenantSettings.objects.update_or_create(
            slug='pizza-shack-x',
            defaults={
                'business_type': 'cafe',
                'business_name': 'The Pizza Shack',
                'tagline': 'Wood-fired pizza on the Northumberland coast',
                'colour_primary': '#dc2626',
                'colour_secondary': '#991b1b',
                'colour_background': '#fffbeb',
                'colour_text': '#1c1917',
                'currency_symbol': '£',
                'phone': '07700 900123',
                'email': 'hello@pizzashack.demo',
                'address': 'The Harbour, Seahouses, Northumberland NE68 7RD',
                'booking_staff_label': 'Chef',
                'booking_staff_label_plural': 'Chefs',
                'enabled_modules': ['orders'],
            },
        )
        self.stdout.write(f'  Tenant: {"created" if created else "updated"}')

        # 2. Create demo users
        for username, role in [('pizza-shack-x-owner', 'owner'), ('pizza-shack-x-staff1', 'staff')]:
            user, ucreated = User.objects.update_or_create(
                username=username,
                defaults={
                    'email': f'{username}@demo.nbne.uk',
                    'role': role,
                    'tenant': tenant,
                    'name': username.replace('-', ' ').title(),
                },
            )
            if ucreated:
                user.set_password('admin123')
                user.save()
            self.stdout.write(f'  User {username}: {"created" if ucreated else "exists"}')

        # 3. Clear old demo data if requested
        if clear:
            Order.objects.filter(tenant=tenant, data_origin='DEMO').delete()
            DailyOrderSummary.objects.filter(tenant=tenant, data_origin='DEMO').delete()
            ItemDailySales.objects.filter(tenant=tenant, data_origin='DEMO').delete()
            self.stdout.write('  Cleared old demo data')

        # 4. Create menu categories and items
        menu_items = {}
        for sort_idx, (cat_name, cat_data) in enumerate(MENU.items()):
            category, _ = MenuCategory.objects.update_or_create(
                tenant=tenant,
                name=cat_name,
                defaults={
                    'sort_order': sort_idx,
                    'icon': cat_data['icon'],
                    'active': True,
                    'data_origin': 'DEMO',
                },
            )
            for item_idx, (name, desc, price, prep, veg, vegan, gf) in enumerate(cat_data['items']):
                item, _ = MenuItem.objects.update_or_create(
                    tenant=tenant,
                    category=category,
                    name=name,
                    defaults={
                        'description': desc,
                        'price_pence': price,
                        'prep_time_minutes': prep,
                        'sort_order': item_idx,
                        'active': True,
                        'vegetarian': veg,
                        'vegan': vegan,
                        'gluten_free': gf,
                        'data_origin': 'DEMO',
                    },
                )
                menu_items[name] = item

        self.stdout.write(f'  Menu: {len(menu_items)} items across {len(MENU)} categories')

        # 5. Create queue settings
        OrderQueueSettings.objects.update_or_create(
            tenant=tenant,
            defaults={
                'current_wait_minutes': 15,
                'auto_calculate_wait': True,
                'avg_prep_time_minutes': 12,
                'max_concurrent_orders': 4,
                'accepting_orders': True,
                'opening_time': datetime.time(12, 0),
                'closing_time': datetime.time(21, 0),
                'accept_card': True,
                'accept_cash': True,
                'accept_bank_transfer': True,
                'bank_transfer_details': 'Pizza Shack Ltd\nSort: 12-34-56\nAccount: 12345678',
            },
        )

        # 6. Generate historical orders
        all_items = list(menu_items.values())
        pizza_items = [i for i in all_items if i.category.name == 'Pizzas']
        side_items = [i for i in all_items if i.category.name == 'Sides']
        dessert_items = [i for i in all_items if i.category.name == 'Desserts']
        drink_items = [i for i in all_items if i.category.name == 'Drinks']

        today = timezone.now().date()
        start_date = today - datetime.timedelta(days=months * 30)
        current_date = start_date
        total_orders = 0
        sources = ['online', 'phone', 'walkin']
        payment_methods = ['card', 'cash', 'bank_transfer']

        self.stdout.write(f'  Generating {months} months of order history...')

        while current_date <= today:
            multiplier = _seasonal_multiplier(current_date)

            # Base: 15-25 orders on a normal summer day
            base_orders = random.randint(15, 25)
            day_orders = max(0, int(base_orders * multiplier))

            if day_orders == 0:
                current_date += datetime.timedelta(days=1)
                continue

            for _ in range(day_orders):
                # Random time between 12:00-20:30
                hour = random.randint(12, 20)
                minute = random.randint(0, 59)
                if hour == 20 and minute > 30:
                    minute = random.randint(0, 30)
                placed_time = timezone.make_aware(
                    datetime.datetime.combine(
                        current_date,
                        datetime.time(hour, minute, random.randint(0, 59)),
                    )
                )

                # Generate order ref
                ref = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

                # Customer
                name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
                phone = f"07{random.randint(100, 999)} {random.randint(100000, 999999)}"

                source = random.choices(sources, weights=[40, 30, 30])[0]
                pay = random.choices(payment_methods, weights=[50, 40, 10])[0]

                order = Order(
                    tenant=tenant,
                    order_ref=ref,
                    customer_name=name,
                    customer_phone=phone,
                    source=source,
                    payment_method=pay,
                    payment_confirmed=True,
                    status='collected',
                    data_origin='DEMO',
                    estimated_ready_minutes=random.randint(10, 25),
                )
                # Bypass auto_now_add
                order.save()
                Order.objects.filter(pk=order.pk).update(placed_at=placed_time)

                # Build order items: 1-3 pizzas + 0-2 sides + 0-1 dessert + 0-2 drinks
                items_to_add = []
                num_pizzas = random.randint(1, 3)
                for pizza in random.sample(pizza_items, min(num_pizzas, len(pizza_items))):
                    items_to_add.append((pizza, random.randint(1, 2)))

                if random.random() < 0.6:
                    for side in random.sample(side_items, min(random.randint(1, 2), len(side_items))):
                        items_to_add.append((side, 1))

                if random.random() < 0.3:
                    dessert = random.choice(dessert_items)
                    items_to_add.append((dessert, 1))

                if random.random() < 0.5:
                    for drink in random.sample(drink_items, min(random.randint(1, 2), len(drink_items))):
                        items_to_add.append((drink, random.randint(1, 2)))

                for item, qty in items_to_add:
                    OrderItem.objects.create(
                        order=order,
                        menu_item=item,
                        name=item.name,
                        quantity=qty,
                        unit_price_pence=item.price_pence,
                    )

                # Calculate totals and set completion times
                order.calculate_totals()
                wait = random.randint(8, 25)
                order.started_at = placed_time + datetime.timedelta(minutes=random.randint(1, 3))
                order.ready_at = placed_time + datetime.timedelta(minutes=wait)
                order.collected_at = placed_time + datetime.timedelta(minutes=wait + random.randint(1, 5))
                order.save()

                total_orders += 1

            # Small % of cancelled orders
            if random.random() < 0.05 and day_orders > 3:
                cancel_count = random.randint(1, max(1, day_orders // 10))
                day_order_qs = Order.objects.filter(
                    tenant=tenant, data_origin='DEMO',
                ).order_by('-id')[:cancel_count]
                for o in day_order_qs:
                    o.status = 'cancelled'
                    o.cancelled_at = o.placed_at + datetime.timedelta(minutes=2)
                    o.save()

            current_date += datetime.timedelta(days=1)

        self.stdout.write(f'  Created {total_orders} historical orders')

        # 7. Build daily summaries
        self.stdout.write('  Building daily summaries...')
        current_date = start_date
        while current_date <= today:
            aggregate_daily_summary(tenant, current_date)
            current_date += datetime.timedelta(days=1)

        # 8. Update item totals
        for item in all_items:
            totals = OrderItem.objects.filter(
                menu_item=item,
                order__tenant=tenant,
                order__status='collected',
            ).aggregate(
                total_qty=models_sum('quantity'),
                total_rev=models_sum_expr(),
            )
            item.total_ordered = totals['total_qty'] or 0
            item.total_revenue_pence = totals['total_rev'] or 0
            item.save()

        self.stdout.write(self.style.SUCCESS(
            f'✅ Pizza Shack X seeded: {len(menu_items)} menu items, '
            f'{total_orders} orders, {months} months of analytics data'
        ))


def models_sum(field):
    from django.db.models import Sum
    return Sum(field)


def models_sum_expr():
    from django.db.models import Sum, F
    return Sum(F('quantity') * F('unit_price_pence'))

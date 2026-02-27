"""
Lightweight command to ensure a tenant record exists without seeding any demo data.
Used in start.sh for live tenants (nbne, mind-department) that must never get demo data.
"""
from django.core.management.base import BaseCommand

# Import the tenant config from seed_demo so we stay DRY
from accounts.management.commands.seed_demo import TENANTS


class Command(BaseCommand):
    help = 'Ensure a tenant settings record exists (no demo data seeded)'

    def add_arguments(self, parser):
        parser.add_argument('slug', type=str, help='Tenant slug to ensure exists')

    def handle(self, *args, **options):
        from tenants.models import TenantSettings

        slug = options['slug']
        cfg = TENANTS.get(slug)
        if not cfg:
            self.stdout.write(self.style.WARNING(f'No config found for tenant "{slug}" — skipping'))
            return

        defaults = {
            'business_name': cfg['business_name'],
            'tagline': cfg['tagline'],
            'colour_primary': cfg['colour_primary'],
            'colour_secondary': cfg['colour_secondary'],
            'email': cfg['email'],
            'phone': cfg['phone'],
            'address': cfg['address'],
            'currency': 'GBP',
            'currency_symbol': '£',
            'deposit_percentage': cfg['deposit_percentage'],
            'enabled_modules': cfg['enabled_modules'],
        }
        for key in ('business_type', 'colour_background', 'colour_text', 'font_heading', 'font_body',
                    'font_url', 'website_url', 'social_instagram',
                    'booking_staff_label', 'booking_staff_label_plural'):
            if key in cfg:
                defaults[key] = cfg[key]

        ts, created = TenantSettings.objects.update_or_create(slug=slug, defaults=defaults)
        self.stdout.write(f'  Tenant: {ts.business_name} ({"created" if created else "updated"}) — no demo data')

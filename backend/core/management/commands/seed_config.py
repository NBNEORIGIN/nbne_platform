from django.core.management.base import BaseCommand
from core.models import Config


class Command(BaseCommand):
    help = 'Seed initial configuration data'

    def handle(self, *args, **kwargs):
        self.stdout.write('🌱 Seeding configuration...')
        
        configs = [
            # Branding
            {'key': 'branding.clientName', 'value': 'NBNE Booking', 'category': 'branding'},
            {'key': 'branding.primaryColor', 'value': '#3B82F6', 'category': 'branding'},
            {'key': 'branding.secondaryColor', 'value': '#10B981', 'category': 'branding'},
            {'key': 'branding.logoUrl', 'value': '/static/logo.png', 'category': 'branding'},
            {'key': 'branding.timezone', 'value': 'UTC', 'category': 'branding'},
            
            # Feature flags
            {'key': 'features.enableSMS', 'value': 'false', 'category': 'features'},
            {'key': 'features.enableWaitlist', 'value': 'true', 'category': 'features'},
            {'key': 'features.enablePortal', 'value': 'true', 'category': 'features'},
            {'key': 'features.bookingType', 'value': 'slots', 'category': 'features'},
            {'key': 'features.maxAdvanceBookingDays', 'value': '30', 'category': 'features'},
        ]
        
        for config_data in configs:
            config, created = Config.objects.update_or_create(
                key=config_data['key'],
                defaults={
                    'value': config_data['value'],
                    'category': config_data['category']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {config.key}'))
            else:
                self.stdout.write(f'  Updated: {config.key}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Configuration seeded successfully!'))

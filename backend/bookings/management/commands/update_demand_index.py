from django.core.management.base import BaseCommand
from bookings.smart_engine import update_service_demand_index


class Command(BaseCommand):
    help = 'Update demand index for all active services (Smart Booking Engine Phase 5)'

    def handle(self, *args, **options):
        self.stdout.write('Updating service demand indices...')
        update_service_demand_index()
        self.stdout.write(self.style.SUCCESS('Demand indices updated.'))

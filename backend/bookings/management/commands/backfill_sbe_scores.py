from django.core.management.base import BaseCommand
from bookings.models import Booking
from bookings.smart_engine import update_reliability_score, calculate_booking_risk, generate_booking_recommendation


class Command(BaseCommand):
    help = 'Backfill Smart Booking Engine scores for existing bookings'

    def handle(self, *args, **options):
        bookings = Booking.objects.filter(risk_score__isnull=True).select_related('client', 'service')
        total = bookings.count()
        self.stdout.write(f'Backfilling {total} bookings...')
        done = 0
        errors = 0
        for booking in bookings:
            try:
                update_reliability_score(booking.client)
                calculate_booking_risk(booking)
                generate_booking_recommendation(booking)
                done += 1
                self.stdout.write(f'  #{booking.id}: risk={booking.risk_score:.1f} level={booking.risk_level}')
            except Exception as e:
                errors += 1
                self.stderr.write(self.style.ERROR(f'  Error on booking #{booking.id}: {type(e).__name__}: {e}'))
        self.stdout.write(self.style.SUCCESS(f'{done}/{total} bookings scored, {errors} errors.'))

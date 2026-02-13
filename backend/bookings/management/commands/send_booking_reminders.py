"""
Management command to send booking reminder emails.
Designed to run every 10 minutes via a background loop or cron.

Usage:
    python manage.py send_booking_reminders          # Run once
    python manage.py send_booking_reminders --loop    # Run continuously (for Railway)
"""
import time
import logging
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send booking reminder emails (24h and 1h before)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loop',
            action='store_true',
            help='Run continuously in a loop (for Railway background worker)',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=None,
            help='Interval in minutes between checks (default: from settings or 10)',
        )

    def handle(self, *args, **options):
        from bookings.email_reminders import process_reminders

        loop = options['loop']
        interval = options['interval'] or getattr(settings, 'REMINDER_INTERVAL_MINUTES', 10)

        if loop:
            self.stdout.write(self.style.SUCCESS(
                f'[REMINDER] Starting reminder loop (every {interval} minutes)'
            ))
            while True:
                try:
                    results = process_reminders()
                    total = results['sent_24h'] + results['sent_1h']
                    if total > 0 or results['failed'] > 0:
                        self.stdout.write(self.style.SUCCESS(
                            f"[REMINDER] 24h: {results['sent_24h']}, 1h: {results['sent_1h']}, "
                            f"failed: {results['failed']}, skipped: {results['skipped']}"
                        ))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'[REMINDER] Error: {e}'))
                    logger.exception('[REMINDER] Unhandled error in reminder loop')

                time.sleep(interval * 60)
        else:
            results = process_reminders()
            self.stdout.write(self.style.SUCCESS(
                f"Reminders sent — 24h: {results['sent_24h']}, 1h: {results['sent_1h']}, "
                f"failed: {results['failed']}, skipped: {results['skipped']}"
            ))

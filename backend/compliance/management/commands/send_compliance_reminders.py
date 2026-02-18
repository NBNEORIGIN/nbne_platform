"""
Management command to send compliance diary reminder emails.
Sends weekly digest to owners/managers about overdue and due-soon items.

Usage:
    python manage.py send_compliance_reminders          # Run once
    python manage.py send_compliance_reminders --loop    # Run continuously (for Railway)
"""
import time
import logging
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)

# Default: check once per day (1440 minutes)
DEFAULT_INTERVAL_MINUTES = 1440


class Command(BaseCommand):
    help = 'Send compliance diary reminder emails (weekly digest to owners/managers)'

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
            help='Interval in minutes between checks (default: 1440 = daily)',
        )

    def handle(self, *args, **options):
        from compliance.email_reminders import process_compliance_reminders

        loop = options['loop']
        interval = options['interval'] or getattr(settings, 'COMPLIANCE_REMINDER_INTERVAL_MINUTES', DEFAULT_INTERVAL_MINUTES)

        if loop:
            self.stdout.write(self.style.SUCCESS(
                f'[COMPLIANCE-REMINDER] Starting reminder loop (every {interval} minutes)'
            ))
            while True:
                try:
                    results = process_compliance_reminders()
                    sent = results['emails_sent']
                    failed = results['emails_failed']
                    if sent > 0 or failed > 0:
                        self.stdout.write(self.style.SUCCESS(
                            f"[COMPLIANCE-REMINDER] Tenants: {results['tenants_checked']}, "
                            f"sent: {sent}, failed: {failed}, skipped: {results['tenants_skipped']}"
                        ))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'[COMPLIANCE-REMINDER] Error: {e}'))
                    logger.exception('[COMPLIANCE-REMINDER] Unhandled error in reminder loop')

                time.sleep(interval * 60)
        else:
            results = process_compliance_reminders()
            self.stdout.write(self.style.SUCCESS(
                f"Compliance reminders — tenants: {results['tenants_checked']}, "
                f"sent: {results['emails_sent']}, failed: {results['emails_failed']}, "
                f"skipped: {results['tenants_skipped']}"
            ))

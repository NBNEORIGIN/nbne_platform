from django.core.management.base import BaseCommand
from compliance.models import PeaceOfMindScore, ScoreAuditLog


class Command(BaseCommand):
    help = 'Recalculate the Peace of Mind compliance score'

    def add_arguments(self, parser):
        parser.add_argument(
            '--trigger',
            type=str,
            default='manual',
            choices=['manual', 'scheduled'],
            help='Trigger type for audit log (default: manual)',
        )

    def handle(self, *args, **options):
        trigger = options['trigger']
        result = PeaceOfMindScore.recalculate()

        # Update the audit log trigger type for the most recent entry
        latest_log = ScoreAuditLog.objects.order_by('-calculated_at').first()
        if latest_log:
            latest_log.trigger = trigger
            latest_log.save(update_fields=['trigger'])

        self.stdout.write(self.style.SUCCESS(
            f'Peace of Mind Score: {result.score}% '
            f'(was {result.previous_score}%) — '
            f'{result.total_items} items '
            f'({result.compliant_count} compliant, '
            f'{result.due_soon_count} due soon, '
            f'{result.overdue_count} overdue)'
        ))

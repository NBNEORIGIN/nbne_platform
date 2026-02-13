"""
Management command: delete_staff_availability_demo
Removes all demo data seeded by seed_staff_availability_demo.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Delete demo data for the staff availability engine'

    def handle(self, *args, **options):
        call_command('seed_staff_availability_demo', '--delete')

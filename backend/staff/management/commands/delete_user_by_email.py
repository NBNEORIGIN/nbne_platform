"""One-off command to delete a user (and their StaffProfile) by email."""
from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = 'Delete a user and their StaffProfile by email address'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email of the user to delete')
        parser.add_argument('--confirm', action='store_true', help='Actually delete (without this flag, dry-run only)')

    def handle(self, *args, **options):
        email = options['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING(f'No user found with email: {email}'))
            return

        self.stdout.write(f'Found user: {user.username} ({user.email}), role={user.role}, tenant={user.tenant}')

        # Check for StaffProfile
        if hasattr(user, 'staff_profile'):
            self.stdout.write(f'  StaffProfile: {user.staff_profile.display_name} (id={user.staff_profile.id})')
        else:
            self.stdout.write('  No StaffProfile attached')

        if options['confirm']:
            user.delete()  # CASCADE will remove StaffProfile too
            self.stdout.write(self.style.SUCCESS(f'Deleted user {email} and all related records.'))
        else:
            self.stdout.write(self.style.WARNING('Dry run — add --confirm to actually delete.'))

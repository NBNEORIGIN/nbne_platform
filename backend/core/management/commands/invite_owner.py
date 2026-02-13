"""
Management command to create an owner account and send an invite email.
Usage: python manage.py invite_owner --email owner@example.com --name "Owner Name"
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models_auth import PasswordToken
from core.auth_views import _send_token_email


class Command(BaseCommand):
    help = 'Create an owner account and send an invite email with a set-password link'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True, help='Owner email address')
        parser.add_argument('--name', required=True, help='Full name (e.g. "Jane Smith")')
        parser.add_argument('--username', default=None, help='Username (defaults to email prefix)')
        parser.add_argument('--resend', action='store_true', help='Resend invite to existing user')

    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        full_name = options['name'].strip()
        parts = full_name.split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''
        username = options['username'] or email.split('@')[0]

        # Check if user exists
        user = User.objects.filter(email__iexact=email).first()

        if user and not options['resend']:
            self.stdout.write(self.style.WARNING(f'User already exists: {user.username} ({user.email})'))
            self.stdout.write('Use --resend to send a new invite email.')
            # Still create token and send
        elif not user:
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            # Set unusable password — forces set-password flow
            user.set_unusable_password()
            # Make owner (superuser + staff)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created owner account: {username} ({email})'))

        # Create invite token and send email
        token_obj = PasswordToken.create_for_user(user, purpose='invite', hours=48)
        self.stdout.write(f'Token: {token_obj.token}')
        self.stdout.write(f'Expires: {token_obj.expires_at}')

        sent = _send_token_email(email, first_name, str(token_obj.token), 'invite')
        if sent:
            self.stdout.write(self.style.SUCCESS(f'Invite email sent to {email}'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to send email to {email}'))
            from django.conf import settings
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            self.stdout.write(f'Manual link: {frontend_url}/set-password?token={token_obj.token}')

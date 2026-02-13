"""
Management command to display current configuration
"""
from django.core.management.base import BaseCommand
from core.config_loader import config
import json


class Command(BaseCommand):
    help = 'Display current client configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--section',
            type=str,
            help='Show specific section (client, branding, booking, features, cancellation)',
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output as JSON',
        )

    def handle(self, *args, **options):
        section = options.get('section')
        as_json = options.get('json')
        
        if section:
            if section == 'client':
                data = config.get_client_info()
            elif section == 'branding':
                data = config.get_branding()
            elif section == 'booking':
                data = config.get_booking_config()
            elif section == 'features':
                data = config.get_features()
            elif section == 'cancellation':
                data = config.get_cancellation_policy()
            else:
                self.stdout.write(self.style.ERROR(f'Unknown section: {section}'))
                return
        else:
            data = config._config
        
        if as_json:
            self.stdout.write(json.dumps(data, indent=2))
        else:
            self._print_config(data, section or 'Configuration')
    
    def _print_config(self, data, title):
        """Pretty print configuration"""
        self.stdout.write(self.style.SUCCESS(f'\n{title}:'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    self.stdout.write(f'\n{key}:')
                    for k, v in value.items():
                        self.stdout.write(f'  {k}: {v}')
                else:
                    self.stdout.write(f'{key}: {value}')
        else:
            self.stdout.write(str(data))
        
        self.stdout.write('\n')

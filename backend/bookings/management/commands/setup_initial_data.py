from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from bookings.models import Service, Staff

User = get_user_model()

class Command(BaseCommand):
    help = 'Create superuser and initial data for House of Hair'

    def handle(self, *args, **kwargs):
        # Create superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'toby@nbnesigns.com', '!49Monkswood')
            self.stdout.write(self.style.SUCCESS('Superuser created'))
        else:
            self.stdout.write('Superuser already exists')

        # Create services
        services_data = [
            {'name': 'Haircut', 'description': 'Professional haircut and styling', 'duration_minutes': 60, 'price': 45.00},
            {'name': 'Color', 'description': 'Full color treatment', 'duration_minutes': 90, 'price': 85.00},
            {'name': 'Highlights', 'description': 'Partial highlights', 'duration_minutes': 120, 'price': 95.00},
            {'name': 'Styling', 'description': 'Special occasion styling', 'duration_minutes': 45, 'price': 35.00},
        ]

        for service_data in services_data:
            service, created = Service.objects.get_or_create(
                name=service_data['name'],
                defaults=service_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created service: {service.name}'))

        # Create staff
        staff_data = [
            {'name': 'Sarah Johnson', 'email': 'sarah@houseofhair.co.uk', 'phone': '01665 123456'},
            {'name': 'Mike Chen', 'email': 'mike@houseofhair.co.uk', 'phone': '01665 123457'},
            {'name': 'Emily Smith', 'email': 'emily@houseofhair.co.uk', 'phone': '01665 123458'},
        ]

        for staff_info in staff_data:
            staff, created = Staff.objects.get_or_create(
                email=staff_info['email'],
                defaults=staff_info
            )
            if created:
                # Add all services to this staff member
                staff.services.set(Service.objects.all())
                self.stdout.write(self.style.SUCCESS(f'Created staff: {staff.name}'))

        self.stdout.write(self.style.SUCCESS('Initial data setup complete!'))

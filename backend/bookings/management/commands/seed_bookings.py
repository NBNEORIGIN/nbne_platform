from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from bookings.models import Service, Staff, Client, Booking, Session


class Command(BaseCommand):
    help = 'Seed booking data for testing'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Seeding booking data...')

        # Create Services
        haircut = Service.objects.update_or_create(
            name='Haircut',
            defaults={
                'description': 'Professional haircut service',
                'duration_minutes': 30,
                'price': 35.00,
                'active': True
            }
        )[0]
        self.stdout.write(f'✓ Created service: {haircut.name}')

        color = Service.objects.update_or_create(
            name='Hair Color',
            defaults={
                'description': 'Full hair coloring service',
                'duration_minutes': 90,
                'price': 85.00,
                'active': True
            }
        )[0]
        self.stdout.write(f'✓ Created service: {color.name}')

        therapy = Service.objects.update_or_create(
            name='Therapy Session',
            defaults={
                'description': 'Individual therapy session',
                'duration_minutes': 60,
                'price': 120.00,
                'active': True
            }
        )[0]
        self.stdout.write(f'✓ Created service: {therapy.name}')

        group = Service.objects.update_or_create(
            name='Group Therapy',
            defaults={
                'description': 'Group therapy session',
                'duration_minutes': 90,
                'price': 45.00,
                'active': True
            }
        )[0]
        self.stdout.write(f'✓ Created service: {group.name}')

        # Create Staff
        sarah = Staff.objects.update_or_create(
            email='sarah@houseofhair.com',
            defaults={
                'name': 'Sarah Johnson',
                'phone': '555-0101',
                'active': True
            }
        )[0]
        sarah.services.add(haircut, color)
        self.stdout.write(f'✓ Created staff: {sarah.name}')

        mike = Staff.objects.update_or_create(
            email='mike@houseofhair.com',
            defaults={
                'name': 'Mike Chen',
                'phone': '555-0102',
                'active': True
            }
        )[0]
        mike.services.add(haircut)
        self.stdout.write(f'✓ Created staff: {mike.name}')

        dr_smith = Staff.objects.update_or_create(
            email='dr.smith@minddept.com',
            defaults={
                'name': 'Dr. Emily Smith',
                'phone': '555-0201',
                'active': True
            }
        )[0]
        dr_smith.services.add(therapy, group)
        self.stdout.write(f'✓ Created staff: {dr_smith.name}')

        # Create Sample Clients
        client1 = Client.objects.update_or_create(
            email='john.doe@example.com',
            defaults={
                'name': 'John Doe',
                'phone': '555-1001',
                'notes': 'Prefers morning appointments'
            }
        )[0]
        self.stdout.write(f'✓ Created client: {client1.name}')

        client2 = Client.objects.update_or_create(
            email='jane.smith@example.com',
            defaults={
                'name': 'Jane Smith',
                'phone': '555-1002',
                'notes': 'Regular customer'
            }
        )[0]
        self.stdout.write(f'✓ Created client: {client2.name}')

        # Create Sample Bookings (tomorrow)
        tomorrow = timezone.now() + timedelta(days=1)
        tomorrow_10am = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        tomorrow_2pm = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)

        booking1 = Booking.objects.update_or_create(
            client=client1,
            service=haircut,
            staff=sarah,
            start_time=tomorrow_10am,
            defaults={
                'status': 'confirmed',
                'notes': 'First appointment'
            }
        )[0]
        self.stdout.write(f'✓ Created booking: {booking1}')

        booking2 = Booking.objects.update_or_create(
            client=client2,
            service=color,
            staff=sarah,
            start_time=tomorrow_2pm,
            defaults={
                'status': 'pending',
                'notes': 'Needs consultation'
            }
        )[0]
        self.stdout.write(f'✓ Created booking: {booking2}')

        # Create Sample Session (next week)
        next_week = timezone.now() + timedelta(days=7)
        next_week_6pm = next_week.replace(hour=18, minute=0, second=0, microsecond=0)
        next_week_730pm = next_week_6pm + timedelta(minutes=90)

        session1 = Session.objects.update_or_create(
            title='Mindfulness & Meditation',
            defaults={
                'description': 'Learn mindfulness techniques and guided meditation',
                'service': group,
                'staff': dr_smith,
                'start_time': next_week_6pm,
                'end_time': next_week_730pm,
                'capacity': 10,
                'active': True
            }
        )[0]
        session1.enrolled_clients.add(client1, client2)
        self.stdout.write(f'✓ Created session: {session1.title}')

        self.stdout.write(self.style.SUCCESS('\n✅ Booking data seeded successfully!'))

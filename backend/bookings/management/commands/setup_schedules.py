from django.core.management.base import BaseCommand
from bookings.models import BusinessHours, StaffSchedule, Staff


class Command(BaseCommand):
    help = 'Initialize default business hours and staff schedules'

    def handle(self, *args, **options):
        # Create default business hours if they don't exist
        for day in range(7):
            BusinessHours.objects.get_or_create(
                day_of_week=day,
                defaults={
                    'is_open': day < 6,  # Mon-Sat open by default
                    'open_time': '09:00',
                    'close_time': '17:00'
                }
            )
        
        self.stdout.write(self.style.SUCCESS('Business hours initialized'))
        
        # Create default schedules for all staff
        staff_members = Staff.objects.all()
        for staff in staff_members:
            for day in range(7):
                StaffSchedule.objects.get_or_create(
                    staff=staff,
                    day_of_week=day,
                    defaults={
                        'is_working': day < 6,  # Mon-Sat working by default
                        'start_time': '09:00',
                        'end_time': '17:00'
                    }
                )
        
        self.stdout.write(self.style.SUCCESS(f'Staff schedules initialized for {staff_members.count()} staff members'))

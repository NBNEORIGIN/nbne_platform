from django.core.management.base import BaseCommand
from crm.models import Lead
from bookings.models import Client, Booking


class Command(BaseCommand):
    help = 'Sync CRM leads from booking clients'

    def handle(self, *args, **options):
        created = 0
        for client in Client.objects.all():
            if Lead.objects.filter(client_id=client.id).exists():
                continue
            bookings = Booking.objects.filter(client=client, status__in=['confirmed', 'completed'])
            total_pence = sum(b.service.price_pence for b in bookings if b.service)
            lead_status = 'CONVERTED' if bookings.filter(status='completed').exists() else 'NEW'
            if bookings.filter(status='confirmed').exists() and lead_status == 'NEW':
                lead_status = 'QUALIFIED'
            Lead.objects.create(
                name=client.name,
                email=client.email,
                phone=client.phone,
                source='booking',
                status=lead_status,
                value_pence=total_pence,
                notes=f'Auto-imported. {bookings.count()} booking(s).',
                client_id=client.id,
            )
            created += 1
        self.stdout.write(self.style.SUCCESS(f'{created} leads synced from bookings'))

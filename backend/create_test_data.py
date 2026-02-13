import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from bookings.models import Service, Staff, IntakeWellbeingDisclaimer, ClassPackage
from django.contrib.auth.models import User
from decimal import Decimal

# Create superuser if it doesn't exist
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@demo.local', 'admin123')
    print("✓ Superuser created: admin")

# Create Service
service, created = Service.objects.get_or_create(
    name='Consultation',
    defaults={
        'description': '60-minute consultation session',
        'duration_minutes': 60,
        'price': Decimal('50.00'),
        'active': True
    }
)
print(f'✓ {"Created" if created else "Found"} service: {service.name}')

# Create Staff
staff, created = Staff.objects.get_or_create(
    email='staff@demo.local',
    defaults={
        'name': 'Demo Staff',
        'phone': '07700900000',
        'active': True
    }
)
staff.services.add(service)
print(f'✓ {"Created" if created else "Found"} staff: {staff.name}')

# Create Disclaimer
disclaimer, created = IntakeWellbeingDisclaimer.objects.get_or_create(
    version='1.0',
    defaults={
        'content': '<p>Our services are designed to support your wellbeing.</p><p><strong>Please note:</strong> Our sessions are not a substitute for medical or psychological treatment. If you have any medical concerns, please consult with a qualified healthcare professional.</p><p>By proceeding, you confirm that you understand the supportive nature of these services.</p>',
        'active': True
    }
)
if created:
    print(f'✓ Created disclaimer: v{disclaimer.version}')
else:
    disclaimer.active = True
    disclaimer.save()
    print(f'✓ Found and activated disclaimer: v{disclaimer.version}')

# Create Class Package
package, created = ClassPackage.objects.get_or_create(
    name='5 Class Pass',
    defaults={
        'description': 'Save 20% with 5 classes',
        'class_count': 5,
        'price': Decimal('100.00'),
        'validity_days': 365,
        'active': True
    }
)
print(f'✓ {"Created" if created else "Found"} package: {package.name}')

print('\n✅ All test data created successfully!')

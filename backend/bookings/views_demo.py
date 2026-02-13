"""
Demo data seed / delete API endpoints.
POST   /api/demo/seed/   — create demo services, clients, bookings
DELETE /api/demo/seed/   — remove all demo data
GET    /api/demo/status/ — check if demo data exists
"""
import uuid
import random
from datetime import timedelta, datetime, time
from decimal import Decimal

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Service, Staff, Client, Booking


# ---------------------------------------------------------------------------
# Demo dataset definitions
# ---------------------------------------------------------------------------

DEMO_SERVICES = [
    {'name': 'Mindfulness Session', 'duration_minutes': 60, 'price': Decimal('45.00'), 'category': 'Mindfulness', 'description': 'Guided mindfulness and meditation session.'},
    {'name': 'Group Breathwork', 'duration_minutes': 45, 'price': Decimal('30.00'), 'category': 'Group', 'description': 'Group breathwork and relaxation class.'},
    {'name': 'Corporate Wellness Workshop', 'duration_minutes': 90, 'price': Decimal('120.00'), 'category': 'Corporate', 'description': 'On-site corporate wellness workshop.'},
]

DEMO_CLIENTS = [
    {'name': 'Alice Demo', 'email': 'alice.demo@example.com', 'phone': '07700100001', 'reliability_score': 95.0},
    {'name': 'Bob Demo', 'email': 'bob.demo@example.com', 'phone': '07700100002', 'reliability_score': 72.0},
    {'name': 'Charlie Demo', 'email': 'charlie.demo@example.com', 'phone': '07700100003', 'reliability_score': 88.0},
    {'name': 'Diana Demo', 'email': 'diana.demo@example.com', 'phone': '07700100004', 'reliability_score': 60.0},
    {'name': 'Eve Demo', 'email': 'eve.demo@example.com', 'phone': '07700100005', 'reliability_score': 98.0},
]

BOOKING_STATUSES = ['confirmed', 'completed', 'completed', 'completed', 'cancelled', 'no_show']
RISK_LEVELS = ['LOW', 'LOW', 'LOW', 'MEDIUM', 'MEDIUM', 'HIGH', 'CRITICAL']


def _build_demo_bookings(seed_id, services, clients, staff_qs):
    """Generate 15-20 demo bookings spread over the last 30 days."""
    now = timezone.now()
    staff_list = list(staff_qs[:4]) or []
    if not staff_list:
        return []

    bookings = []
    num = random.randint(15, 20)
    for i in range(num):
        svc = random.choice(services)
        client = random.choice(clients)
        staff = random.choice(staff_list)
        days_ago = random.randint(0, 29)
        hour = random.choice([9, 10, 11, 13, 14, 15, 16])
        start = (now - timedelta(days=days_ago)).replace(
            hour=hour, minute=0, second=0, microsecond=0
        )
        end = start + timedelta(minutes=svc.duration_minutes)
        status = random.choice(BOOKING_STATUSES)
        risk = random.choice(RISK_LEVELS)
        risk_score = {'LOW': random.uniform(0, 25), 'MEDIUM': random.uniform(25, 50),
                      'HIGH': random.uniform(50, 75), 'CRITICAL': random.uniform(75, 100)}[risk]
        rev_at_risk = Decimal(str(round(float(svc.price) * risk_score / 100, 2)))

        bookings.append(Booking(
            client=client, service=svc, staff=staff,
            start_time=start, end_time=end,
            status=status, notes='Demo booking',
            risk_score=round(risk_score, 1), risk_level=risk,
            revenue_at_risk=rev_at_risk,
            payment_status='paid' if status == 'completed' else 'pending',
            payment_amount=svc.price if status == 'completed' else None,
            data_origin='DEMO', demo_seed_id=seed_id,
        ))
    return bookings


# ---------------------------------------------------------------------------
# API views
# ---------------------------------------------------------------------------

@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def demo_seed_view(request):
    """POST = seed demo data, DELETE = remove all demo data."""

    if request.method == 'DELETE':
        Booking.objects.filter(data_origin='DEMO').delete()
        Client.objects.filter(data_origin='DEMO').delete()
        Service.objects.filter(data_origin='DEMO').delete()
        has_real = Booking.objects.filter(data_origin='REAL').exists()
        return Response({'deleted': True, 'has_real': has_real})

    # POST — seed
    # Idempotent: if demo data already exists, return current status
    existing_demo = Booking.objects.filter(data_origin='DEMO').count()
    if existing_demo > 0:
        return Response({
            'has_demo': True,
            'has_real': Booking.objects.filter(data_origin='REAL').exists(),
            'demo_count': existing_demo,
        })

    seed_id = uuid.uuid4()

    # Create demo services
    demo_services = []
    for svc_data in DEMO_SERVICES:
        svc = Service.objects.create(
            **svc_data, active=True,
            data_origin='DEMO', demo_seed_id=seed_id,
        )
        demo_services.append(svc)

    # Assign demo services to existing staff
    staff_qs = Staff.objects.filter(active=True)
    for staff in staff_qs[:4]:
        staff.services.add(*demo_services)

    # Create demo clients
    demo_clients = []
    for cl_data in DEMO_CLIENTS:
        cl = Client.objects.create(
            **cl_data,
            data_origin='DEMO', demo_seed_id=seed_id,
        )
        demo_clients.append(cl)

    # Create demo bookings
    demo_bookings = _build_demo_bookings(seed_id, demo_services, demo_clients, staff_qs)
    Booking.objects.bulk_create(demo_bookings)

    demo_count = Booking.objects.filter(data_origin='DEMO').count()
    return Response({
        'has_demo': True,
        'has_real': Booking.objects.filter(data_origin='REAL').exists(),
        'demo_count': demo_count,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def demo_status_view(request):
    """Return whether demo data exists."""
    demo_count = Booking.objects.filter(data_origin='DEMO').count()
    return Response({
        'has_demo': demo_count > 0,
        'has_real': Booking.objects.filter(data_origin='REAL').exists(),
        'demo_count': demo_count,
    })

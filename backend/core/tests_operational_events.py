"""
Tests for the Operational Event Aggregation Service.
Verifies event detection for bookings, staff leave, and compliance deltas.
"""
from datetime import timedelta
from decimal import Decimal
from django.test import TestCase, override_settings
from django.utils import timezone


@override_settings(
    BOOKINGS_MODULE_ENABLED=True,
    STAFF_MODULE_ENABLED=True,
    COMPLIANCE_MODULE_ENABLED=True,
)
class OperationalEventsTest(TestCase):

    def setUp(self):
        from bookings.models import Service, Staff, Client, Booking
        self.service = Service.objects.create(
            name='Test Service', duration_minutes=60, price=Decimal('50.00'),
        )
        self.staff = Staff.objects.create(
            name='Alice', email='alice@test.local', role='staff', active=True,
        )
        self.staff.services.add(self.service)
        self.client = Client.objects.create(
            name='Bob Customer', email='bob@test.local', phone='07700 000000',
        )

    def _create_booking(self, **kwargs):
        from bookings.models import Booking
        now = timezone.now()
        defaults = {
            'client': self.client,
            'service': self.service,
            'staff': self.staff,
            'start_time': now.replace(hour=10, minute=0, second=0, microsecond=0),
            'end_time': now.replace(hour=11, minute=0, second=0, microsecond=0),
            'status': 'confirmed',
            'payment_status': 'paid',
        }
        defaults.update(kwargs)
        return Booking.objects.create(**defaults)

    # -----------------------------------------------------------------
    # Sorted state (no events)
    # -----------------------------------------------------------------
    def test_no_events_returns_sorted(self):
        from core.operational_events import get_operational_events, get_dashboard_state
        events = get_operational_events()
        state = get_dashboard_state(events)
        self.assertEqual(state['state'], 'sorted')
        self.assertIn('No active issues', state['message'])

    # -----------------------------------------------------------------
    # Booking cancelled today
    # -----------------------------------------------------------------
    def test_cancelled_booking_generates_event(self):
        from core.operational_events import get_operational_events
        b = self._create_booking(status='cancelled')
        events = get_operational_events()
        cancelled = [e for e in events if e['event_type'] == 'booking_cancelled']
        self.assertEqual(len(cancelled), 1)
        self.assertEqual(cancelled[0]['severity'], 'warning')
        self.assertIn('Bob Customer', cancelled[0]['summary'])

    # -----------------------------------------------------------------
    # Unassigned booking
    # -----------------------------------------------------------------
    def test_unassigned_booking_generates_critical_event(self):
        from core.operational_events import get_operational_events
        self._create_booking(staff=None)
        events = get_operational_events()
        unassigned = [e for e in events if e['event_type'] == 'booking_unassigned']
        self.assertEqual(len(unassigned), 1)
        self.assertIn(unassigned[0]['severity'], ['critical', 'high'])
        # Should suggest Alice as available staff
        action_labels = [a['label'] for a in unassigned[0]['actions']]
        self.assertTrue(any('Alice' in l for l in action_labels))

    # -----------------------------------------------------------------
    # Deposit missing
    # -----------------------------------------------------------------
    def test_unpaid_booking_generates_deposit_event(self):
        from core.operational_events import get_operational_events
        self._create_booking(payment_status='pending')
        events = get_operational_events()
        deposit = [e for e in events if e['event_type'] == 'deposit_missing']
        self.assertEqual(len(deposit), 1)
        self.assertEqual(deposit[0]['severity'], 'high')
        self.assertIn('£50.00', deposit[0]['summary'])

    def test_free_service_no_deposit_event(self):
        from bookings.models import Service
        from core.operational_events import get_operational_events
        free_svc = Service.objects.create(
            name='Free Consultation', duration_minutes=30, price=Decimal('0.00'),
        )
        self._create_booking(service=free_svc, payment_status='pending')
        events = get_operational_events()
        deposit = [e for e in events if e['event_type'] == 'deposit_missing']
        self.assertEqual(len(deposit), 0)

    # -----------------------------------------------------------------
    # Staff sick leave
    # -----------------------------------------------------------------
    def test_sick_leave_generates_critical_event(self):
        from bookings.models_availability import LeaveRequest
        from core.operational_events import get_operational_events
        now = timezone.now()
        LeaveRequest.objects.create(
            staff_member=self.staff,
            leave_type='SICK',
            start_datetime=now.replace(hour=0, minute=0),
            end_datetime=now.replace(hour=23, minute=59),
            status='APPROVED',
        )
        events = get_operational_events()
        sick = [e for e in events if e['event_type'] == 'staff_sick']
        self.assertEqual(len(sick), 1)
        self.assertEqual(sick[0]['severity'], 'critical')
        self.assertIn('Alice', sick[0]['summary'])

    # -----------------------------------------------------------------
    # Pending leave request
    # -----------------------------------------------------------------
    def test_pending_leave_generates_warning(self):
        from bookings.models_availability import LeaveRequest
        from core.operational_events import get_operational_events
        now = timezone.now()
        tomorrow = now + timedelta(days=1)
        LeaveRequest.objects.create(
            staff_member=self.staff,
            leave_type='ANNUAL',
            start_datetime=tomorrow.replace(hour=9, minute=0),
            end_datetime=tomorrow.replace(hour=17, minute=0),
            status='REQUESTED',
        )
        events = get_operational_events()
        pending = [e for e in events if e['event_type'] == 'leave_pending']
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]['severity'], 'warning')

    # -----------------------------------------------------------------
    # Compliance overdue
    # -----------------------------------------------------------------
    def test_overdue_compliance_generates_event(self):
        from compliance.models import ComplianceCategory, ComplianceItem
        from core.operational_events import get_operational_events
        cat = ComplianceCategory.objects.create(name='Test Category', max_score=10)
        # Disconnect signals to avoid recursion during test
        from django.db.models.signals import post_save, post_delete
        from compliance.signals import recalculate_score_on_save, recalculate_score_on_delete
        post_save.disconnect(recalculate_score_on_save)
        post_delete.disconnect(recalculate_score_on_delete)
        try:
            ComplianceItem.objects.create(
                title='Expired Certificate',
                category=cat,
                item_type='LEGAL',
                status='OVERDUE',
                next_due_date=timezone.now().date() - timedelta(days=10),
            )
            events = get_operational_events()
            comp = [e for e in events if e['event_type'] == 'compliance_expiry']
            self.assertTrue(len(comp) >= 1)
            overdue_evt = [e for e in comp if 'Overdue' in e['summary']]
            self.assertEqual(len(overdue_evt), 1)
            self.assertIn(overdue_evt[0]['severity'], ['critical', 'high'])
        finally:
            post_save.connect(recalculate_score_on_save)
            post_delete.connect(recalculate_score_on_delete)

    # -----------------------------------------------------------------
    # Open incident
    # -----------------------------------------------------------------
    def test_open_incident_generates_event(self):
        from django.contrib.auth import get_user_model
        from compliance.models import IncidentReport
        from core.operational_events import get_operational_events
        User = get_user_model()
        user = User.objects.create_user('testuser', 'test@test.local', 'pass123')
        IncidentReport.objects.create(
            title='Wet floor',
            description='Water near entrance',
            severity='HIGH',
            status='OPEN',
            location='Reception',
            incident_date=timezone.now(),
            reported_by=user,
        )
        events = get_operational_events()
        incidents = [e for e in events if e['event_type'] == 'incident_open']
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]['severity'], 'critical')

    # -----------------------------------------------------------------
    # Dashboard state
    # -----------------------------------------------------------------
    def test_active_state_with_events(self):
        from core.operational_events import get_operational_events, get_dashboard_state
        self._create_booking(status='cancelled')
        events = get_operational_events()
        state = get_dashboard_state(events)
        self.assertEqual(state['state'], 'active')

    # -----------------------------------------------------------------
    # Severity ordering
    # -----------------------------------------------------------------
    def test_events_sorted_by_severity(self):
        from bookings.models_availability import LeaveRequest
        from core.operational_events import get_operational_events
        now = timezone.now()
        # Create a warning event (cancelled booking)
        self._create_booking(status='cancelled')
        # Create a critical event (sick leave)
        LeaveRequest.objects.create(
            staff_member=self.staff,
            leave_type='SICK',
            start_datetime=now.replace(hour=0, minute=0),
            end_datetime=now.replace(hour=23, minute=59),
            status='APPROVED',
        )
        events = get_operational_events()
        if len(events) >= 2:
            severities = [e['severity'] for e in events]
            severity_order = {'critical': 0, 'high': 1, 'warning': 2, 'info': 3}
            ordered = all(
                severity_order.get(severities[i], 99) <= severity_order.get(severities[i+1], 99)
                for i in range(len(severities) - 1)
            )
            self.assertTrue(ordered, f'Events not sorted by severity: {severities}')


@override_settings(
    BOOKINGS_MODULE_ENABLED=False,
    STAFF_MODULE_ENABLED=False,
    COMPLIANCE_MODULE_ENABLED=False,
)
class OperationalEventsDisabledModulesTest(TestCase):

    def test_no_events_when_modules_disabled(self):
        from core.operational_events import get_operational_events, get_dashboard_state
        events = get_operational_events()
        self.assertEqual(len(events), 0)
        state = get_dashboard_state(events)
        self.assertEqual(state['state'], 'sorted')

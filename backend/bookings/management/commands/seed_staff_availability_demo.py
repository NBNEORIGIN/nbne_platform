"""
Management command: seed_staff_availability_demo
Seeds realistic demo data for the staff availability engine.
All demo data is tagged with demo_seed_id for clean removal.
"""
import uuid
from datetime import date, time, datetime, timedelta
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.utils import timezone

from bookings.models import Staff, Service, Client, Booking
from bookings.models_availability import (
    WorkingPattern, WorkingPatternRule,
    AvailabilityOverride, AvailabilityOverridePeriod,
    LeaveRequest, BlockedTime, Shift, TimesheetEntry,
)

UK_TZ = ZoneInfo('Europe/London')

# Unique tag so we can find and delete all demo availability data
DEMO_TAG = 'avail-demo'


def _aware(d, t):
    """Combine date + time into tz-aware datetime in Europe/London."""
    return datetime.combine(d, t, tzinfo=UK_TZ)


class Command(BaseCommand):
    help = 'Seed demo data for the staff availability engine'

    def add_arguments(self, parser):
        parser.add_argument('--delete', action='store_true', help='Delete demo availability data instead of seeding')

    def handle(self, *args, **options):
        if options['delete']:
            self._delete()
            return
        self._seed()

    def _delete(self):
        """Remove all demo availability data tagged with DEMO_TAG."""
        counts = {}
        counts['TimesheetEntry'] = TimesheetEntry.objects.filter(notes__contains=DEMO_TAG).delete()[0]
        counts['Shift'] = Shift.objects.filter(notes__contains=DEMO_TAG).delete()[0]
        counts['BlockedTime'] = BlockedTime.objects.filter(reason__contains=DEMO_TAG).delete()[0]
        counts['LeaveRequest'] = LeaveRequest.objects.filter(reason__contains=DEMO_TAG).delete()[0]
        counts['AvailabilityOverridePeriod'] = AvailabilityOverridePeriod.objects.filter(
            availability_override__reason__contains=DEMO_TAG
        ).delete()[0]
        counts['AvailabilityOverride'] = AvailabilityOverride.objects.filter(reason__contains=DEMO_TAG).delete()[0]
        counts['WorkingPatternRule'] = WorkingPatternRule.objects.filter(
            working_pattern__name__contains=DEMO_TAG
        ).delete()[0]
        counts['WorkingPattern'] = WorkingPattern.objects.filter(name__contains=DEMO_TAG).delete()[0]
        # Demo bookings (for slot testing)
        counts['Booking'] = Booking.objects.filter(notes__contains=DEMO_TAG).delete()[0]

        total = sum(counts.values())
        self.stdout.write(self.style.SUCCESS(f'Deleted {total} demo availability records'))
        for model, count in counts.items():
            if count:
                self.stdout.write(f'  {model}: {count}')

    def _seed(self):
        """Seed realistic demo availability data."""
        # Check if demo data already exists
        if WorkingPattern.objects.filter(name__contains=DEMO_TAG).exists():
            self.stdout.write(self.style.WARNING('Demo availability data already exists. Use --delete first.'))
            return

        # Get or create 3 staff members
        staff_members = list(Staff.objects.filter(active=True)[:3])
        if len(staff_members) < 2:
            self.stdout.write(self.style.ERROR('Need at least 2 active staff members. Create staff first.'))
            return

        today = date.today()
        next_monday = today + timedelta(days=(7 - today.weekday()) % 7 or 7)

        self.stdout.write('Seeding demo availability data...')

        # ── A) Working Patterns ──────────────────────────────────────
        patterns_created = 0
        rules_created = 0

        # Staff 1: Standard 9-5 Mon-Fri
        s1 = staff_members[0]
        p1 = WorkingPattern.objects.create(
            staff_member=s1,
            name=f'Standard Week [{DEMO_TAG}]',
            is_active=True,
        )
        for day in range(5):  # Mon-Fri
            WorkingPatternRule.objects.create(
                working_pattern=p1, weekday=day,
                start_time=time(9, 0), end_time=time(17, 0), sort_order=0,
            )
            rules_created += 1
        patterns_created += 1

        # Staff 2: Split shift Mon-Fri (9-12, 14-18) + Saturday morning
        s2 = staff_members[1]
        p2 = WorkingPattern.objects.create(
            staff_member=s2,
            name=f'Split Shift [{DEMO_TAG}]',
            is_active=True,
        )
        for day in range(5):  # Mon-Fri
            WorkingPatternRule.objects.create(
                working_pattern=p2, weekday=day,
                start_time=time(9, 0), end_time=time(12, 0), sort_order=0,
            )
            WorkingPatternRule.objects.create(
                working_pattern=p2, weekday=day,
                start_time=time(14, 0), end_time=time(18, 0), sort_order=1,
            )
            rules_created += 2
        # Saturday morning
        WorkingPatternRule.objects.create(
            working_pattern=p2, weekday=5,
            start_time=time(9, 0), end_time=time(13, 0), sort_order=0,
        )
        rules_created += 1
        patterns_created += 1

        # Staff 3 (if exists): Part-time Tue/Thu/Fri
        if len(staff_members) >= 3:
            s3 = staff_members[2]
            p3 = WorkingPattern.objects.create(
                staff_member=s3,
                name=f'Part-Time [{DEMO_TAG}]',
                is_active=True,
            )
            for day in [1, 3, 4]:  # Tue, Thu, Fri
                WorkingPatternRule.objects.create(
                    working_pattern=p3, weekday=day,
                    start_time=time(10, 0), end_time=time(16, 0), sort_order=0,
                )
                rules_created += 1
            patterns_created += 1

        self.stdout.write(f'  Created {patterns_created} working patterns with {rules_created} rules')

        # ── B) Availability Overrides ────────────────────────────────
        overrides_created = 0

        # ADD override: Staff 1 works extra evening next Wednesday
        wed = next_monday + timedelta(days=2)
        ov_add = AvailabilityOverride.objects.create(
            staff_member=s1, date=wed, mode='ADD',
            reason=f'Extra evening session [{DEMO_TAG}]',
        )
        AvailabilityOverridePeriod.objects.create(
            availability_override=ov_add,
            start_time=time(18, 0), end_time=time(20, 0), sort_order=0,
        )
        overrides_created += 1

        # REMOVE override: Staff 2 has a dentist appointment next Tuesday 10-11
        tue = next_monday + timedelta(days=1)
        ov_remove = AvailabilityOverride.objects.create(
            staff_member=s2, date=tue, mode='REMOVE',
            reason=f'Dentist appointment [{DEMO_TAG}]',
        )
        AvailabilityOverridePeriod.objects.create(
            availability_override=ov_remove,
            start_time=time(10, 0), end_time=time(11, 0), sort_order=0,
        )
        overrides_created += 1

        # CLOSED override: Staff 1 closed next Friday (personal day)
        fri = next_monday + timedelta(days=4)
        AvailabilityOverride.objects.create(
            staff_member=s1, date=fri, mode='CLOSED',
            reason=f'Personal day [{DEMO_TAG}]',
        )
        overrides_created += 1

        # REPLACE override: Staff 2 works different hours next Thursday
        thu = next_monday + timedelta(days=3)
        ov_replace = AvailabilityOverride.objects.create(
            staff_member=s2, date=thu, mode='REPLACE',
            reason=f'Covering for colleague [{DEMO_TAG}]',
        )
        AvailabilityOverridePeriod.objects.create(
            availability_override=ov_replace,
            start_time=time(7, 0), end_time=time(15, 0), sort_order=0,
        )
        overrides_created += 1

        self.stdout.write(f'  Created {overrides_created} availability overrides')

        # ── C) Leave Request (APPROVED) ──────────────────────────────
        # Staff 2: approved half-day leave next Monday afternoon
        LeaveRequest.objects.create(
            staff_member=s2,
            leave_type='ANNUAL',
            start_datetime=_aware(next_monday, time(13, 0)),
            end_datetime=_aware(next_monday, time(18, 0)),
            status='APPROVED',
            reason=f'Half-day annual leave [{DEMO_TAG}]',
        )
        # Staff 1: requested (not approved) sick leave — should NOT block
        LeaveRequest.objects.create(
            staff_member=s1,
            leave_type='SICK',
            start_datetime=_aware(next_monday + timedelta(days=7), time(0, 0)),
            end_datetime=_aware(next_monday + timedelta(days=7), time(23, 59)),
            status='REQUESTED',
            reason=f'Feeling unwell [{DEMO_TAG}]',
        )
        self.stdout.write(f'  Created 2 leave requests (1 APPROVED, 1 REQUESTED)')

        # ── D) Blocked Time ──────────────────────────────────────────
        # Global block: fire drill next Tuesday 11:00-11:30
        BlockedTime.objects.create(
            staff_member=None,
            start_datetime=_aware(tue, time(11, 0)),
            end_datetime=_aware(tue, time(11, 30)),
            reason=f'Fire drill (all staff) [{DEMO_TAG}]',
        )
        # Staff-specific block: Staff 1 meeting next Thursday 14-15
        BlockedTime.objects.create(
            staff_member=s1,
            start_datetime=_aware(thu, time(14, 0)),
            end_datetime=_aware(thu, time(15, 0)),
            reason=f'Team meeting [{DEMO_TAG}]',
        )
        self.stdout.write(f'  Created 2 blocked times (1 global, 1 staff-specific)')

        # ── E) Shifts (rota) ─────────────────────────────────────────
        shifts_created = 0
        # Staff 1: shift next Monday
        Shift.objects.create(
            staff_member=s1,
            start_datetime=_aware(next_monday, time(9, 0)),
            end_datetime=_aware(next_monday, time(17, 0)),
            location='Main Office',
            published=True,
            notes=f'Regular shift [{DEMO_TAG}]',
        )
        shifts_created += 1
        # Staff 2: split shift next Monday
        Shift.objects.create(
            staff_member=s2,
            start_datetime=_aware(next_monday, time(9, 0)),
            end_datetime=_aware(next_monday, time(12, 0)),
            location='Main Office',
            published=True,
            notes=f'Morning shift [{DEMO_TAG}]',
        )
        Shift.objects.create(
            staff_member=s2,
            start_datetime=_aware(next_monday, time(14, 0)),
            end_datetime=_aware(next_monday, time(18, 0)),
            location='Main Office',
            published=True,
            notes=f'Afternoon shift [{DEMO_TAG}]',
        )
        shifts_created += 2
        self.stdout.write(f'  Created {shifts_created} shifts')

        # ── F) Timesheets ────────────────────────────────────────────
        ts_created = 0
        # Last Monday timesheets
        last_monday = today - timedelta(days=today.weekday())
        if last_monday == today:
            last_monday -= timedelta(days=7)

        TimesheetEntry.objects.create(
            staff_member=s1, date=last_monday,
            scheduled_start=_aware(last_monday, time(9, 0)),
            scheduled_end=_aware(last_monday, time(17, 0)),
            actual_start=_aware(last_monday, time(8, 55)),
            actual_end=_aware(last_monday, time(17, 10)),
            break_minutes=60,
            status='APPROVED',
            source='GENERATED_FROM_PATTERN',
            notes=f'Auto-generated [{DEMO_TAG}]',
        )
        ts_created += 1

        TimesheetEntry.objects.create(
            staff_member=s2, date=last_monday,
            scheduled_start=_aware(last_monday, time(9, 0)),
            scheduled_end=_aware(last_monday, time(18, 0)),
            actual_start=_aware(last_monday, time(9, 10)),
            actual_end=_aware(last_monday, time(17, 45)),
            break_minutes=120,
            status='SUBMITTED',
            source='GENERATED_FROM_SHIFT',
            notes=f'Split shift day [{DEMO_TAG}]',
        )
        ts_created += 1
        self.stdout.write(f'  Created {ts_created} timesheet entries')

        # ── G) Sample bookings (for slot testing) ────────────────────
        services = list(Service.objects.filter(active=True)[:2])
        clients = list(Client.objects.all()[:2])
        bk_created = 0
        if services and clients and len(staff_members) >= 2:
            # Booking on next Monday morning for staff 1
            Booking.objects.create(
                client=clients[0], service=services[0], staff=s1,
                start_time=_aware(next_monday, time(10, 0)),
                end_time=_aware(next_monday, time(10, 0)) + timedelta(minutes=services[0].duration_minutes),
                status='confirmed',
                notes=f'Demo booking [{DEMO_TAG}]',
                data_origin='DEMO',
            )
            bk_created += 1
            # Booking on next Monday for staff 2
            Booking.objects.create(
                client=clients[-1], service=services[-1], staff=s2,
                start_time=_aware(next_monday, time(9, 30)),
                end_time=_aware(next_monday, time(9, 30)) + timedelta(minutes=services[-1].duration_minutes),
                status='confirmed',
                notes=f'Demo booking [{DEMO_TAG}]',
                data_origin='DEMO',
            )
            bk_created += 1
        self.stdout.write(f'  Created {bk_created} sample bookings')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Demo availability data seeded for {len(staff_members)} staff members.\n'
            f'Next Monday reference date: {next_monday}\n'
            f'Use --delete to remove all demo availability data.'
        ))

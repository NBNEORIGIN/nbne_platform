# WIGGUM Loop: Configurable Booking Engine by Business Type

## Context

The NBNE platform is a multi-tenant SaaS serving salons, restaurants, and gyms. Currently the booking page (`frontend/app/book/page.tsx`) is hardcoded to a salon-style linear flow: Service → Staff → Date → Time → Details. This works for salons but is wrong for restaurants (need party size + table matching) and gyms (need class timetable + capacity).

### What already exists (DO NOT duplicate or replace)

- `backend/tenants/models.py` → `TenantSettings` model with `slug`, `business_name`, `booking_staff_label`, `booking_staff_label_plural`, `enabled_modules`, `business_hours`, `deposit_percentage`, etc.
- `backend/bookings/models.py` → `Service` (with `category`, `duration_minutes`, `price`, `deposit_pence`), `Staff`, `Client`, `Booking`, `Session` (group classes with `capacity`, `enrolled_clients`), `BusinessHours`, `StaffSchedule`, `Closure`, `StaffBlock`, `StaffLeave`
- `backend/bookings/models_availability.py` → `WorkingPattern`, `WorkingPatternRule`, `AvailabilityOverride`, `BlockedTime`, `Shift`, `TimesheetEntry`
- `frontend/lib/tenant.tsx` → `TenantConfig` interface with `booking_staff_label`, `booking_staff_label_plural`, exposed via `useTenant()` hook
- `frontend/lib/api.ts` → `getServices()`, `getBookableStaff()`, `getStaffSlots()`, `getSlots()`, `createBooking()`, `createCheckoutSession()`
- `backend/tenants/serializers.py` → `TenantSettingsSerializer`, `TenantSettingsUpdateSerializer`, `TenantSettingsCSSVarsSerializer`
- `backend/accounts/management/commands/seed_demo.py` → Seed data for `salon-x`, `restaurant-x`, `health-club-x`, `mind-department`, `nbne`

### Tech stack

- Backend: Django 5 + DRF, PostgreSQL, deployed on Railway
- Frontend: Next.js 14 (App Router), React, inline styles (no Tailwind in booking page), deployed on Vercel
- Tenant resolution: `NEXT_PUBLIC_TENANT_SLUG` env var → Next.js proxy adds `?tenant=slug` + `X-Tenant-Slug` header to Django requests

---

## Loop 9: Configurable Booking Engine

### Loop 9.1: Add `business_type` to TenantSettings

**Scope:** Backend model + serializer + migration + seed data + frontend type

Add a `business_type` field to `TenantSettings`:

```python
BUSINESS_TYPE_CHOICES = [
    ('salon', 'Salon / Beauty'),
    ('restaurant', 'Restaurant / Hospitality'),
    ('gym', 'Gym / Fitness'),
    ('generic', 'Generic / Other'),
]
business_type = models.CharField(max_length=20, choices=BUSINESS_TYPE_CHOICES, default='salon')
```

Changes required:
1. `backend/tenants/models.py` — Add field to `TenantSettings`
2. `backend/tenants/serializers.py` — Add `business_type` to all three serializers
3. Create migration `backend/tenants/migrations/0004_tenantsettings_business_type.py`
4. `backend/accounts/management/commands/seed_demo.py` — Set `business_type` per tenant:
   - `salon-x` → `'salon'`
   - `restaurant-x` → `'restaurant'`
   - `health-club-x` → `'gym'`
   - `mind-department` → `'generic'`
   - `nbne` → `'generic'`
   - Add `'business_type'` to the optional keys loop in `_seed_tenant`
5. `frontend/lib/tenant.tsx` — Add `business_type: string` to `TenantConfig` interface and `DEFAULT_CONFIG` (default `'salon'`)

**Exit criteria:**
- `GET /api/config/branding/` returns `business_type` for each tenant
- `useTenant().business_type` available in frontend
- All seed tenants have correct `business_type` set
- No existing functionality broken

---

### Loop 9.2: Restaurant models — `Table` and `ServiceWindow`

**Scope:** Backend models + migration + admin API endpoints + seed data

Create two new models in `backend/bookings/models.py` (or a new `models_restaurant.py` and import into `models.py`):

```python
class Table(models.Model):
    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, related_name='tables')
    name = models.CharField(max_length=100)  # "Table 1", "Window Booth", "Terrace 3"
    min_seats = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    max_seats = models.IntegerField(default=4, validators=[MinValueValidator(1)])
    combinable = models.BooleanField(default=False, help_text='Can be combined with adjacent table')
    combine_with = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, help_text='Adjacent table for combining')
    zone = models.CharField(max_length=100, blank=True, default='', help_text='e.g. Main, Terrace, Private')
    active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class ServiceWindow(models.Model):
    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, related_name='service_windows')
    name = models.CharField(max_length=100)  # "Lunch", "Dinner", "Brunch"
    day_of_week = models.IntegerField(choices=[(i, d) for i, d in enumerate(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])])
    open_time = models.TimeField()
    close_time = models.TimeField()
    last_booking_time = models.TimeField(help_text='Latest time a booking can start')
    turn_time_minutes = models.IntegerField(default=90, help_text='Default dining duration in minutes')
    max_covers = models.IntegerField(default=50, help_text='Max total covers in this window')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

API endpoints (add to `bookings/views.py` or new `bookings/views_restaurant.py`):
- `GET /api/bookings/tables/` — List tables for tenant (admin)
- `POST/PUT/DELETE /api/bookings/tables/<id>/` — CRUD (admin)
- `GET /api/bookings/service-windows/` — List service windows for tenant
- `POST/PUT/DELETE /api/bookings/service-windows/<id>/` — CRUD (admin)
- `GET /api/bookings/restaurant-availability/?date=YYYY-MM-DD&party_size=N` — Public endpoint: returns available time slots for a given date and party size, checking table inventory against existing bookings

Seed data for `restaurant-x`:
- Tables: 8-10 tables (mix of 2-tops, 4-tops, 6-tops, one private dining room)
- Service windows: Lunch (12:00-14:30) and Dinner (18:00-22:00) for each day, closed Monday

**Exit criteria:**
- Models created with migration
- CRUD endpoints work for admin users
- Restaurant availability endpoint returns correct time slots based on table inventory
- `restaurant-x` seed data includes tables and service windows
- Salon and gym tenants unaffected

---

### Loop 9.3: Gym class booking models — `ClassType` and `ClassSession`

**Scope:** Backend models + migration + API endpoints + seed data

The existing `Session` model is close but lacks timetable recurrence. Create in `backend/bookings/models_gym.py`:

```python
class ClassType(models.Model):
    """Recurring class definition — e.g. 'Monday 6pm HIIT'"""
    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, related_name='class_types')
    service = models.ForeignKey('Service', on_delete=models.CASCADE, related_name='class_type_links')
    instructor = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True, related_name='class_types')
    day_of_week = models.IntegerField(choices=[(i, d) for i, d in enumerate(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])])
    start_time = models.TimeField()
    capacity = models.IntegerField(default=20, validators=[MinValueValidator(1)])
    location = models.CharField(max_length=100, blank=True, default='', help_text='e.g. Studio 1, Main Gym')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ClassSession(models.Model):
    """Concrete instance of a ClassType on a specific date"""
    class_type = models.ForeignKey(ClassType, on_delete=models.CASCADE, related_name='sessions')
    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, related_name='class_sessions')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    instructor = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True)
    capacity_override = models.IntegerField(null=True, blank=True, help_text='Override class_type capacity for this session')
    cancelled = models.BooleanField(default=False)
    enrolled_clients = models.ManyToManyField('Client', blank=True, related_name='class_sessions')
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def effective_capacity(self):
        return self.capacity_override or self.class_type.capacity

    @property
    def spots_remaining(self):
        return max(0, self.effective_capacity - self.enrolled_clients.count())

    @property
    def is_full(self):
        return self.spots_remaining == 0
```

API endpoints:
- `GET /api/bookings/class-types/` — List class types (admin + public)
- `POST/PUT/DELETE /api/bookings/class-types/<id>/` — CRUD (admin)
- `GET /api/bookings/class-sessions/?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD` — Public: list sessions in date range with spots remaining
- `POST /api/bookings/class-sessions/<id>/enroll/` — Public: enroll client in session (check capacity)
- Management command or cron: Generate `ClassSession` instances from `ClassType` templates for the next N weeks

Seed data for `health-club-x`:
- ClassTypes: HIIT (Mon/Wed/Fri 6pm), Yoga (Tue/Thu 7am), Spin (Mon/Wed 12pm), Boxing (Tue/Thu 6pm), Pilates (Sat 9am), CrossFit (Mon-Fri 7am)
- Generate ClassSessions for next 4 weeks from ClassTypes

**Exit criteria:**
- Models created with migration
- Timetable CRUD endpoints work
- Class session listing shows spots remaining
- Enrollment endpoint enforces capacity
- `health-club-x` seed data includes class types and generated sessions
- Salon and restaurant tenants unaffected

---

### Loop 9.4: Frontend — Booking flow router

**Scope:** Frontend only — route to correct booking flow based on `business_type`

Refactor `frontend/app/book/page.tsx`:

1. Extract the current booking flow into `frontend/app/book/SalonBookingFlow.tsx` (move existing code, no logic changes)
2. Create `frontend/app/book/page.tsx` as a thin router:

```tsx
'use client'
import { Suspense } from 'react'
import { useTenant } from '@/lib/tenant'
import SalonBookingFlow from './SalonBookingFlow'
import RestaurantBookingFlow from './RestaurantBookingFlow'
import GymBookingFlow from './GymBookingFlow'

function BookRouter() {
  const tenant = useTenant()
  switch (tenant.business_type) {
    case 'restaurant': return <RestaurantBookingFlow />
    case 'gym': return <GymBookingFlow />
    default: return <SalonBookingFlow />
  }
}

export default function BookPage() {
  return (
    <Suspense fallback={<div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Loading...</div>}>
      <BookRouter />
    </Suspense>
  )
}
```

3. Create stub components for `RestaurantBookingFlow.tsx` and `GymBookingFlow.tsx` that just render a placeholder message: "Restaurant/Gym booking coming soon — use the salon flow for now". They should still render the header with tenant branding.

**Exit criteria:**
- Salon X (`business_type: 'salon'`) renders existing booking flow unchanged
- Tavola (`business_type: 'restaurant'`) renders restaurant placeholder
- FitHub (`business_type: 'gym'`) renders gym placeholder
- No regression in salon booking flow
- Shared components (header, Section, Calendar) extracted if reused

---

### Loop 9.5: Frontend — Restaurant booking flow

**Scope:** `frontend/app/book/RestaurantBookingFlow.tsx`

Flow: Party Size → Date → Time Window → Details → Confirm

Steps:
1. **Party size** — Number selector (1-20), prominent display
2. **Date** — Reuse Calendar component from salon flow
3. **Time** — Call `GET /api/bookings/restaurant-availability/?date=X&party_size=N`, show available time slots grouped by service window (Lunch / Dinner). Each slot shows the time. Grey out full slots.
4. **Details** — Name, email, phone, notes, dietary requirements (new field)
5. **Confirm** — Create booking via existing `POST /api/bookings/` endpoint. The `service` should be auto-selected based on party size (map to "Book a Table", "Table for 4-6", or "Large Party (7+)" from seed services). The `staff` should be auto-assigned (any available host).

Design: Match the existing booking page aesthetic — use the same `SERIF`, `SANS`, `ACCENT`, `BG_CREAM` tokens. Use the tenant's branding colours where the salon flow uses hardcoded salon colours. Read colours from `useTenant()`.

**Exit criteria:**
- Full restaurant booking flow works end-to-end on Tavola
- Party size drives table matching
- Time slots respect service window hours and table availability
- Booking created in database with correct tenant, service, staff
- Mobile responsive
- Stripe deposit flow works if service has deposit

---

### Loop 9.6: Frontend — Gym booking flow

**Scope:** `frontend/app/book/GymBookingFlow.tsx`

Flow: Browse Classes → Pick Session → Details → Confirm

Steps:
1. **Browse classes** — Show a weekly timetable view. Columns = days (Mon-Sun), rows = time slots. Each cell shows class name, instructor, spots remaining. Alternatively: a list view grouped by day with filter by class type.
2. **Pick session** — Clicking a class session selects it. Show details: class name, instructor, time, duration, spots remaining, price.
3. **Details** — Name, email, phone (reuse from salon flow)
4. **Confirm** — Call `POST /api/bookings/class-sessions/<id>/enroll/` to enroll. If the class has a price > 0, integrate with Stripe checkout.

Also show a separate section for **1:1 bookings** (Personal Training, Sports Massage, etc.) that uses the existing salon-style flow: Service → Trainer → Date → Time → Details. Filter services to categories that are 1:1 (not "Classes" or "Memberships").

Design: Bold, high-energy aesthetic matching FitHub's brand. Use tenant branding colours. Dark backgrounds, strong contrast, uppercase headings.

**Exit criteria:**
- Class timetable displays correctly with real data
- Session enrollment enforces capacity (shows "Full" badge, disables booking)
- 1:1 PT booking works via existing staff-based flow
- Booking/enrollment created in database
- Mobile responsive

---

### Loop 9.7: Admin UI — Business type selector + onboarding checklist

**Scope:** Frontend admin panel

Add to the admin Settings page (or as a new "Setup" page):

1. **Business type selector** — 3 cards (Salon, Restaurant, Gym) + Generic. Selecting one calls `PATCH /api/config/settings/` to update `business_type`. Show current selection with a checkmark. Warn if changing type: "This will change your booking page layout. Your existing data will be kept."

2. **Onboarding checklist** — Dynamic based on `business_type`:

   **Salon:**
   - [ ] Add your services → link to Services page
   - [ ] Add your staff → link to Staff page
   - [ ] Set opening hours → link to Settings
   - [ ] Configure deposits/payments → link to Settings
   - [ ] Customise your booking page → link to Settings (colours, logo)

   **Restaurant:**
   - [ ] Set up your tables → link to new Tables admin page
   - [ ] Configure service windows (lunch/dinner) → link to new Service Windows admin page
   - [ ] Add your menu/services → link to Services page
   - [ ] Add your hosts → link to Staff page
   - [ ] Configure deposits → link to Settings

   **Gym:**
   - [ ] Add your class types → link to new Class Types admin page
   - [ ] Set up your timetable → link to new Timetable admin page
   - [ ] Add your trainers → link to Staff page
   - [ ] Add 1:1 services (PT, massage) → link to Services page
   - [ ] Configure memberships → link to Services page

   Each item checks real data: e.g. "Add your services" is checked if `services.count() > 0`.

3. **Admin pages for new entities:**
   - Tables management page (restaurant only) — CRUD table inventory
   - Service Windows management page (restaurant only) — CRUD lunch/dinner windows
   - Class Types management page (gym only) — CRUD class definitions
   - Timetable view (gym only) — Weekly grid showing class sessions, ability to cancel/modify individual sessions

   These pages should only be visible in the admin sidebar when the tenant's `business_type` matches.

**Exit criteria:**
- Business type can be changed from admin
- Checklist items reflect real data state
- New admin pages work for restaurant and gym entities
- Sidebar shows/hides pages based on business type
- No regression in existing admin functionality

---

## Implementation Order

Execute loops **strictly in order** 9.1 → 9.2 → 9.3 → 9.4 → 9.5 → 9.6 → 9.7. Each loop builds on the previous.

## Key Constraints

- **DO NOT** create a separate `BusinessTypePreset` model. The `business_type` field on `TenantSettings` is sufficient.
- **DO NOT** store booking flow config as JSON blobs. The flow variants are code (React components), not data.
- **DO NOT** break existing salon booking flow. It must continue to work identically.
- **DO NOT** add new npm dependencies without justification. Use existing inline styles pattern.
- **DO** reuse existing models (`Service`, `Staff`, `Client`, `Booking`) where possible. Restaurant and gym bookings should still create `Booking` records.
- **DO** maintain tenant isolation — all new models must have a `tenant` FK.
- **DO** add new fields to seed_demo.py so demo sites have realistic data.
- **DO** write the migration files manually if `makemigrations` fails (the dev environment doesn't have DB_NAME configured — see existing pattern in `backend/tenants/migrations/0003_tenantsettings_booking_staff_label.py`).

## Files You'll Touch

**Backend:**
- `backend/tenants/models.py` — Add `business_type` field
- `backend/tenants/serializers.py` — Expose `business_type`
- `backend/tenants/migrations/` — New migration(s)
- `backend/bookings/models.py` or new `models_restaurant.py`, `models_gym.py` — New models
- `backend/bookings/views.py` or new view files — New API endpoints
- `backend/bookings/urls.py` — New URL patterns
- `backend/accounts/management/commands/seed_demo.py` — Seed data updates

**Frontend:**
- `frontend/lib/tenant.tsx` — Add `business_type` to interface
- `frontend/app/book/page.tsx` — Refactor to router
- `frontend/app/book/SalonBookingFlow.tsx` — Extracted existing flow
- `frontend/app/book/RestaurantBookingFlow.tsx` — New
- `frontend/app/book/GymBookingFlow.tsx` — New
- `frontend/lib/api.ts` — New API functions for restaurant/gym endpoints
- `frontend/app/admin/` — New admin pages for tables, service windows, class types

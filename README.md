# NBNE Business Platform — Revision 3

> **Comprehensive reference for stress-testing and automated QA.**
> This document describes every module, API endpoint, data model, authentication flow, known issue, and deployment detail needed to write and execute end-to-end tests against the platform.

---

## 1. Platform Overview

A **multi-tenant SaaS platform** for small UK businesses (salons, restaurants, gyms, generic). One shared Django backend serves multiple Next.js frontends — each identified by a `NEXT_PUBLIC_TENANT_SLUG` env var. Tenants get their own branding, enabled modules, users, and data.

| Layer | Stack | Host | URL pattern |
|-------|-------|------|-------------|
| Backend API | Django 5.2 + DRF 3.14 + SimpleJWT | Railway | `https://nbneplatform-production.up.railway.app` |
| Database | PostgreSQL 16 | Railway (managed) | Internal |
| Frontend | Next.js 14.2.21 + React 18 + TypeScript | Vercel | `https://<site>.vercel.app` |
| Payments | Stripe Checkout Sessions | Stripe | External |
| Email | Resend HTTP API (Railway blocks SMTP) | Resend | External |
| Static | WhiteNoise | Railway | `/static/` |
| Media | Railway volume at `/data/media` | Railway | `/media/` |
| Admin UI | Jazzmin (Django admin theme) | Railway | `/admin/` |

---

## 2. Deployment Architecture

```
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ Vercel            │   │ Vercel            │   │ Vercel            │
│ salon-x2          │   │ tavola-gray       │   │ fithub-lake       │
│ TENANT=salon-x    │   │ TENANT=restaurant-x│  │ TENANT=health-..  │
└────────┬─────────┘   └────────┬──────────┘   └────────┬─────────┘
         │                      │                        │
         └──────────────────────┼────────────────────────┘
                                │
                   ┌────────────▼────────────┐
                   │  Railway                 │
                   │  Django API (all on)     │
                   │  PostgreSQL              │
                   │  /data/media volume      │
                   └─────────────────────────┘
```

### Live Demo Sites

| Tenant slug | Vercel domain | Business type | Enabled modules |
|-------------|---------------|---------------|-----------------|
| `salon-x` | `salon-x2.vercel.app` | salon | bookings, payments, staff, comms, compliance, analytics, shop |
| `restaurant-x` | `tavola-gray.vercel.app` | restaurant | bookings, staff, crm, compliance, analytics, shop |
| `health-club-x` | `fithub-lake.vercel.app` | gym | bookings, payments, staff, comms, compliance, documents, analytics, shop |
| `nbne` | `nbne-business.vercel.app` | generic | All modules (internal dogfooding) |

### Demo Credentials (all sites)

| Email | Password | Role | Access |
|-------|----------|------|--------|
| `owner@demo.local` | `admin123` | Owner | Full admin (`/admin/*`) |
| `manager@demo.local` | `admin123` | Manager | Full admin (`/admin/*`) |
| `staff1@demo.local` | `admin123` | Staff | Staff portal (`/app/*`) |

---

## 3. Multi-Tenancy

### Tenant Resolution (Backend)

Implemented in `core/middleware_tenant.py` — `TenantMiddleware`:

1. **`X-Tenant-Slug` header** (sent by frontend proxy — always wins)
2. **`?tenant=` query param** (backward compat / demo pages)
3. **Authenticated user → `user.tenant`** (fallback for Django admin)
4. **First tenant in DB** (last resort)

Every model with tenant-scoped data has a `tenant = ForeignKey('tenants.TenantSettings')` field. All querysets filter by `request.tenant`.

### Tenant Resolution (Frontend)

- `NEXT_PUBLIC_TENANT_SLUG` env var set per Vercel deployment
- `TenantProvider` (React context) fetches `/api/django/tenant/branding/` on mount
- Injects branding (colours, fonts, business name) into CSS variables
- `hasModule(tenant, mod)` controls nav visibility
- Frontend proxy at `/api/django/[...path]/route.ts` injects `X-Tenant-Slug` header

### TenantSettings Model Fields

```
slug, business_type, business_name, enabled_modules (JSON array),
tagline, logo_url, favicon_url,
colour_primary, colour_secondary, colour_accent, colour_background, colour_text,
font_heading, font_body, font_url,
email, phone, address, website_url,
social_facebook, social_instagram, social_twitter,
business_hours (JSON), booking_staff_label, booking_staff_label_plural,
booking_lead_time_hours, booking_max_advance_days,
cancellation_policy, deposit_percentage, currency, currency_symbol,
pwa_theme_colour, pwa_background_colour, pwa_short_name
```

---

## 4. Authentication & RBAC

### Auth Flow

1. `POST /api/auth/login/` with `{ username, password }` → returns `{ access, refresh, user }`
2. Access token (JWT, 8h lifetime) stored in `localStorage` as `nbne_access`
3. Refresh token (7d lifetime) stored as `nbne_refresh`
4. All API calls include `Authorization: Bearer <access>` header
5. On 401, frontend auto-refreshes via `POST /api/auth/refresh/`
6. Middleware cookie `nbne_session` gates `/admin/*` (manager+) and `/app/*` (staff+)

### Role Hierarchy

| Role | Tier | Access |
|------|------|--------|
| `customer` | 1 | Public pages only |
| `staff` | 2 | `/app/*` (staff portal) |
| `manager` | 2-3 | `/admin/*` (admin panel) |
| `owner` | 3 | `/admin/*` (full admin) |

### User Model (`accounts.User`)

Extends `AbstractUser`:
```
tenant (FK), role, phone, bio, avatar_initials, is_active_staff, must_change_password
```

---

## 5. Backend Modules & API Endpoints

### 5.1 Core (always enabled)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/login/` | No | JWT login |
| GET | `/api/auth/me/` | Yes | Current user info |
| POST | `/api/auth/me/set-password/` | Yes | Change password |
| POST | `/api/auth/password-reset/` | No | Request reset email |
| GET | `/api/auth/validate-token/` | No | Check token validity |
| POST | `/api/auth/set-password-token/` | No | Set password via token |
| POST | `/api/auth/invite/` | Yes | Send owner invite |
| GET | `/api/auth/users/` | Yes | List users (admin) |
| GET | `/api/tenant/branding/` | No | Get tenant branding |
| GET | `/api/tenant/` | No | Get tenant settings |
| GET | `/api/dashboard/today/` | Yes | Operational dashboard V2 |
| POST | `/api/events/log/` | Yes | Log business event |
| GET | `/api/events/today/` | Yes | Today's resolved events |
| POST | `/api/events/decline/` | Yes | Decline cover request |
| POST | `/api/assistant/parse/` | Yes | Parse command text |
| POST | `/api/assistant/chat/` | Yes | AI chat (OpenAI) |
| POST | `/api/command/` | Yes | Execute global command |
| GET | `/api/command/suggestions/` | Yes | Command bar suggestions |
| POST | `/api/contact/` | No | Public contact form |
| POST | `/api/beta-signup/` | No | Beta signup form |
| POST | `/api/feedback/` | Yes | Submit feedback |
| GET | `/api/audit/` | Yes | Audit log |

### 5.2 Bookings (`BOOKINGS_MODULE_ENABLED`)

**DRF Router endpoints** (all under `/api/`):
| Resource | Basename | Notes |
|----------|----------|-------|
| `/services/` | service | CRUD + public read |
| `/staff/` | staff | CRUD |
| `/bookings/` | booking | CRUD + confirm/cancel/complete/no-show/assign-staff actions |
| `/clients/` | client | CRUD |
| `/staff-blocks/` | staff-block | CRUD |
| `/business-hours/` | — | CRUD |
| `/staff-schedules/` | — | CRUD |
| `/closures/` | — | CRUD |
| `/staff-leave/` | — | CRUD |
| `/intake/` | — | Intake profiles |
| `/intake-disclaimer/` | — | Wellbeing disclaimers |
| `/packages/` | — | Class packages |
| `/credits/` | — | Client credits |
| `/payment/` | payment | Payment integrations |
| `/sessions/` | session | Sessions |
| `/tables/` | table | Restaurant tables |
| `/service-windows/` | service-window | Restaurant service windows |
| `/class-types/` | class-type | Gym class types |
| `/class-sessions/` | class-session | Gym class sessions |
| `/working-patterns/` | working-pattern | Availability |
| `/working-pattern-rules/` | working-pattern-rule | Availability |
| `/availability-overrides/` | availability-override | Availability |
| `/leave-requests/` | leave-request | Leave requests |
| `/blocked-times/` | blocked-time | Blocked times |
| `/shifts/` | shift | Shifts |
| `/timesheets/` | timesheet | Timesheet entries |

**Custom endpoints:**
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/bookings/slots/` | Yes | Get available booking slots |
| POST | `/api/bookings/create/` | No | Create a booking |
| GET | `/api/restaurant-availability/` | No | Restaurant slot availability |
| GET | `/api/restaurant-available-dates/` | No | Available dates for party size |
| GET | `/api/gym-timetable/` | No | Gym timetable |
| GET | `/api/gym-class-types/` | No | Public class types |
| POST | `/api/checkout/create/` | No | Stripe checkout session |
| POST | `/api/checkout/webhook/` | No | Stripe webhook |
| GET | `/api/dashboard-summary/` | Yes | Dashboard metrics |
| POST | `/api/backfill-sbe/` | Yes | Backfill SBE scores |
| GET | `/api/reports/overview/` | Yes | Reports overview |
| GET | `/api/reports/daily/` | Yes | Daily revenue report |
| GET | `/api/reports/monthly/` | Yes | Monthly report |
| GET | `/api/reports/staff/` | Yes | Staff performance |
| GET | `/api/reports/insights/` | Yes | AI-powered insights |
| GET | `/api/reports/staff-hours/` | Yes | Staff hours report |
| GET | `/api/reports/staff-hours/csv/` | Yes | CSV export |
| GET | `/api/reports/leave/` | Yes | Leave report |
| GET | `/api/availability/` | Yes | Staff availability |
| GET | `/api/availability/slots/` | Yes | Free slots |
| GET | `/api/staff/working-hours/` | Yes | Working hours list |
| POST | `/api/staff/working-hours/bulk-set/` | Yes | Bulk set working hours |
| DELETE | `/api/staff/working-hours/<id>/delete/` | Yes | Delete working hours |
| GET | `/api/staff/timesheets/` | Yes | Timesheets list |
| POST | `/api/staff/timesheets/generate/` | Yes | Generate timesheets |
| GET | `/api/staff/timesheets/summary/` | Yes | Timesheet summary |
| PATCH | `/api/staff/timesheets/<id>/update/` | Yes | Update timesheet |
| POST | `/api/demo/seed/` | Yes | Seed demo data |
| GET | `/api/demo/status/` | Yes | Demo data status |
| POST | `/api/demo/availability/seed/` | Yes | Seed availability |

### 5.3 Staff (`STAFF_MODULE_ENABLED`)

All under `/api/staff-module/`:
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List staff |
| POST | `/create/` | Create staff member |
| PATCH | `/<id>/update/` | Update staff |
| DELETE | `/<id>/delete/` | Delete staff |
| GET | `/shifts/` | List shifts |
| POST | `/shifts/create/` | Create shift |
| PATCH | `/shifts/<id>/update/` | Update shift |
| DELETE | `/shifts/<id>/delete/` | Delete shift |
| GET | `/my-shifts/` | Current user's shifts |
| GET | `/leave/` | Leave requests |
| POST | `/leave/create/` | Create leave request |
| POST | `/leave/<id>/review/` | Approve/reject leave |
| DELETE | `/leave/<id>/delete/` | Delete leave request |
| GET | `/leave/calendar/` | Leave calendar |
| GET | `/absence/` | Absences |
| GET | `/training/` | Training records |
| POST | `/training/create/` | Add training record |
| DELETE | `/training/<id>/delete/` | Delete training record |
| GET | `/training/reminders/` | Expiring training |
| GET | `/training/compliance/` | Training compliance matrix |
| GET | `/training/courses/` | Training courses |
| POST | `/training/courses/create/` | Create course |
| PUT | `/training/courses/<id>/update/` | Update course |
| DELETE | `/training/courses/<id>/delete/` | Delete course |
| GET | `/working-hours/` | Working hours |
| POST | `/working-hours/bulk-set/` | Bulk set |
| DELETE | `/working-hours/<id>/delete/` | Delete |
| GET | `/timesheets/` | Timesheet list |
| PATCH | `/timesheets/<id>/update/` | Update timesheet |
| POST | `/timesheets/generate/` | Generate timesheets |
| GET | `/timesheets/summary/` | Summary |
| POST | `/timesheets/quick-log/` | Quick time log |
| GET | `/timesheets/export/` | CSV export |
| GET | `/project-codes/` | Project codes |
| POST | `/project-codes/create/` | Create project code |
| PATCH | `/project-codes/<id>/update/` | Update |
| DELETE | `/project-codes/<id>/delete/` | Delete |
| GET | `/payroll/summary/` | Payroll summary |
| GET | `/hours-tally/` | Hours credit/deficit |
| GET | `/leave-balance/` | Leave balance |

### 5.4 Comms (`COMMS_MODULE_ENABLED`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/comms/channels/` | Yes | List channels |
| GET | `/api/comms/channels/<id>/messages/` | Yes | Channel messages |
| POST | `/api/comms/channels/<id>/messages/create/` | Yes | Send message (supports file attachments via FormData) |
| POST | `/api/comms/ensure-general/` | Yes | Ensure general channel exists |

### 5.5 Compliance (`COMPLIANCE_MODULE_ENABLED`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/compliance/dashboard/` | Yes | Compliance dashboard |
| GET | `/api/compliance/dashboard-v2/` | Yes | V2 dashboard |
| GET | `/api/compliance/wiggum/` | Yes | Wiggum dashboard |
| GET | `/api/compliance/categories/` | Yes | Compliance categories |
| POST | `/api/compliance/categories/create/` | Yes | Create category |
| GET | `/api/compliance/items/` | Yes | Compliance items |
| POST | `/api/compliance/items/create/` | Yes | Create item |
| POST | `/api/compliance/items/<id>/complete/` | Yes | Mark complete (supports FormData evidence) |
| POST | `/api/compliance/items/<id>/assign/` | Yes | Assign to user |
| DELETE | `/api/compliance/items/<id>/delete/` | Yes | Delete item |
| GET | `/api/compliance/my-actions/` | Yes | My assigned actions |
| GET | `/api/compliance/my-training/` | Yes | My training |
| GET | `/api/compliance/training/` | Yes | Training list |
| GET | `/api/compliance/documents/` | Yes | Compliance documents |
| GET | `/api/compliance/logs/` | Yes | Action logs |
| GET | `/api/compliance/incidents/` | Yes | Incidents |
| POST | `/api/compliance/incidents/create/` | Yes | Create incident |
| POST | `/api/compliance/incidents/<id>/photo/` | Yes | Upload photo (FormData) |
| POST | `/api/compliance/incidents/<id>/status/` | Yes | Update incident status |
| POST | `/api/compliance/parse-command/` | Yes | Parse compliance command |
| GET | `/api/compliance/calendar/` | Yes | Compliance calendar |
| GET | `/api/compliance/audit-log/` | Yes | Compliance audit log |
| POST | `/api/compliance/recalculate/` | Yes | Recalculate score |
| GET | `/api/compliance/rams/` | Yes | RAMS documents |
| GET | `/api/compliance/accidents/` | Yes | Accident book |
| POST | `/api/compliance/accidents/create/` | Yes | Create accident record |
| PATCH | `/api/compliance/accidents/<id>/update/` | Yes | Update accident |
| DELETE | `/api/compliance/accidents/<id>/delete/` | Yes | Delete accident |

### 5.6 Documents (`DOCUMENTS_MODULE_ENABLED`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/documents/` | Yes | List documents |
| GET | `/api/documents/summary/` | Yes | Document summary stats |
| POST | `/api/documents/create/` | Yes | Upload document (FormData) |
| PATCH | `/api/documents/<id>/` | Yes | Update document (FormData) |
| DELETE | `/api/documents/<id>/` | Yes | Delete document |
| GET | `/api/documents/<id>/download/` | Yes | Download file |
| GET | `/api/documents/tags/` | Yes | List tags |
| POST | `/api/documents/tags/create/` | Yes | Create tag |
| GET | `/api/documents/expiring/` | Yes | Expiring documents |

### 5.7 CRM (`CRM_MODULE_ENABLED`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/crm/leads/` | Yes | List leads |
| POST | `/api/crm/leads/create/` | Yes | Create lead |
| POST | `/api/crm/leads/<id>/update/` | Yes | Update lead |
| POST | `/api/crm/leads/<id>/status/` | Yes | Update lead status |
| POST | `/api/crm/leads/quick-add/` | Yes | Quick add lead from text |
| POST | `/api/crm/leads/<id>/contact/` | Yes | Mark contacted |
| POST | `/api/crm/leads/<id>/convert/` | Yes | Convert lead |
| POST | `/api/crm/leads/<id>/followup-done/` | Yes | Mark followup done |
| GET | `/api/crm/leads/<id>/notes/` | Yes | Lead notes |
| POST | `/api/crm/leads/<id>/notes/` | Yes | Add note |
| GET | `/api/crm/leads/<id>/history/` | Yes | Lead history |
| GET | `/api/crm/revenue/` | Yes | Revenue stats |
| GET | `/api/crm/leads/<id>/revenue/` | Yes | Lead revenue |

### 5.8 Shop (`SHOP_MODULE_ENABLED`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/shop/products/` | No | List products (admin sees all, public sees active) |
| POST | `/api/shop/products/` | Yes | Create product (JSON) |
| GET | `/api/shop/products/<id>/` | No | Product detail |
| PATCH | `/api/shop/products/<id>/` | Yes | Update product |
| DELETE | `/api/shop/products/<id>/` | Yes | Delete product |
| POST | `/api/shop/products/<id>/images/` | Yes | Upload images (multipart, field: `images`) |
| DELETE | `/api/shop/products/<id>/images/<img_id>/` | Yes | Delete image |
| POST | `/api/shop/products/<id>/images/reorder/` | Yes | Reorder images `{ "order": [id, id, ...] }` |
| GET | `/api/shop/orders/` | Yes | List orders |
| PATCH | `/api/shop/orders/<id>/` | Yes | Update order (e.g. status) |
| POST | `/api/shop/checkout/` | No | Create checkout (see payload below) |
| GET | `/api/shop/public/products/` | No | Public active products (with `?category=` filter) |

**Checkout payload:**
```json
{
  "items": [{ "product_id": 1, "quantity": 2 }],
  "customer_name": "John",
  "customer_email": "john@example.com",
  "customer_phone": "07700000000"
}
```

**Checkout behaviour:**
- If `STRIPE_SECRET_KEY` is set → creates Stripe Checkout Session, returns `{ checkout_url, order_id }`
- If Stripe not configured → marks order as `paid` immediately, returns `{ order_id, status: "paid" }`
- Stock is deducted on checkout, not on payment confirmation (known limitation)

### 5.9 Payments (`PAYMENTS_MODULE_ENABLED`)

Under `/api/payments/` — Stripe webhook handling and payment record management.

### 5.10 Tenants (`TENANTS_MODULE_ENABLED`)

Under `/api/tenants/` — tenant CRUD (admin only).

---

## 6. Data Models

### Core
- **User** — `tenant`, `role` (customer/staff/manager/owner), `phone`, `bio`, `avatar_initials`, `must_change_password`

### Tenants
- **TenantSettings** — `slug` (unique), `business_type`, `business_name`, `enabled_modules` (JSON), branding fields, booking config, PWA config

### Bookings
- **Service** — name, description, duration_minutes, price_pence, deposit_pence, category, active, tenant
- **Booking** — customer info, service, slot, status, staff assignment, notes, tenant
- **Client** — name, email, phone, notes, tenant
- **Table** — name, capacity, active (restaurant)
- **ServiceWindow** — name, day, start/end times (restaurant)
- **ClassType** — name, description, duration, capacity (gym)
- **ClassSession** — class type, day, time, instructor (gym)
- **IntakeProfile** — customer wellbeing data, GDPR consent
- **ClassPackage** — multi-session pass with credit tracking

### Staff
- **StaffProfile** — linked to User, department, hourly_rate, employment_type
- **Shift** — staff, date, start/end times, location
- **LeaveRequest** — staff, type, dates, status
- **TrainingRecord** — staff, title, provider, dates
- **TrainingCourse** — template for training
- **TimesheetEntry** — staff, date, hours, breaks
- **ProjectCode** — billing codes for timesheets

### Compliance
- **ComplianceCategory** — name, description, weight
- **ComplianceItem** — category, title, status, assigned_to, due_date, evidence
- **Incident** — title, severity, status, reporter, photos
- **IncidentPhoto** — incident FK, image, caption
- **Accident** — accident book entries

### Documents
- **Document** — title, category, file, uploaded_by, expiry_date, tags
- **DocumentTag** — name, colour

### CRM
- **Lead** — name, email, phone, source, status, value, notes, tenant
- **LeadNote** — lead FK, text, author
- **LeadHistory** — lead FK, action, timestamp

### Comms
- **Channel** — name, type (GENERAL/TEAM/DIRECT), members
- **Message** — channel, sender, body, attachments
- **MessageAttachment** — message FK, file, filename

### Shop
- **Product** — `tenant`, `name`, `subtitle`, `description`, `category`, `price` (Decimal), `compare_at_price`, `image_url` (legacy), `stock_quantity`, `track_stock`, `sort_order`, `active`
- **ProductImage** — `product` FK, `image` (ImageField → `shop/products/%Y/%m/`), `alt_text`, `sort_order`
- **Order** — `tenant`, `customer_name`, `customer_email`, `customer_phone`, `status` (pending/paid/processing/shipped/completed/cancelled/refunded), `total_pence`, `stripe_session_id`, `stripe_payment_intent`, `notes`
- **OrderItem** — `order` FK, `product` FK (SET_NULL), `product_name` (snapshot), `quantity`, `unit_price_pence`

---

## 7. Frontend Architecture

### Tech Stack
- Next.js 14.2.21, React 18, TypeScript 5.3
- No component library — all inline styles
- JWT auth stored in localStorage (`nbne_access`, `nbne_refresh`)
- Cookie `nbne_session` for middleware route protection
- `jose` for JWT handling, `bcryptjs` for demo auth

### API Client (`frontend/lib/api.ts`)

- `apiFetch<T>(path, options)` — core fetcher with JWT auth, cache-busting, auto-refresh
- `apiUpload<T>(path, formData, method)` — multipart uploads (no Content-Type header)
- All calls go through Vercel proxy at `/api/django/[...path]/route.ts`
- Proxy injects `X-Tenant-Slug` header and forwards auth
- Trailing-slash enforcement to avoid Django 301 redirects
- Cache-bust `_cb=<timestamp>` on every request

### Route Structure

**Public (no auth):**
| Route | Description |
|-------|-------------|
| `/` | NBNE platform landing page |
| `/salon` | Salon X demo landing page |
| `/restaurant` | Restaurant X demo landing page |
| `/gym` | Health Club X demo landing page |
| `/book` | Public booking page |
| `/services` | Public services list |
| `/shop` | Public shop — product grid, cart, checkout |
| `/shop/success` | Post-purchase confirmation |
| `/login` | Login page |
| `/reset-password` | Password reset |
| `/set-password` | Set password via token |
| `/pricing` | Platform pricing page |

**Staff portal (`/app/*` — requires `staff` role):**
| Route | Description |
|-------|-------------|
| `/app` | Staff dashboard, shifts, leave |

**Admin panel (`/admin/*` — requires `manager` role):**
| Route | Description |
|-------|-------------|
| `/admin` | Owner dashboard (revenue, bookings, incidents) |
| `/admin/bookings` | Booking management |
| `/admin/reports` | Revenue/utilisation/retention reports |
| `/admin/services` | Service CRUD |
| `/admin/tables` | Restaurant table management |
| `/admin/service-windows` | Restaurant service windows |
| `/admin/class-types` | Gym class type management |
| `/admin/timetable` | Gym timetable |
| `/admin/staff` | Staff management (3 sub-tabs) |
| `/admin/clients` | CRM / lead management |
| `/admin/chat` | Team messaging |
| `/admin/health-safety` | HSE compliance (6 sub-pages) |
| `/admin/documents` | Document vault |
| `/admin/shop` | Product + order management |
| `/admin/audit` | Audit log viewer |
| `/admin/settings` | Tenant settings |

### Middleware (`frontend/middleware.ts`)

- Runs on every request (except static assets)
- API routes: adds `_mcb` cache-bust param, no-cache headers
- Protected routes: checks `nbne_session` cookie, decodes JWT, validates role + tenant + expiry
- Cross-tenant check: rejects if `payload.tenant_slug !== NEXT_PUBLIC_TENANT_SLUG`
- Attaches `x-user-id`, `x-user-role`, `x-user-name` headers to downstream

### Admin Sidebar Nav

Items are filtered by `hasModule(tenant, module)` and `businessType` match:
```
Dashboard    (always)       Bookings  (bookings)
Reports      (bookings)     Services  (bookings)
Tables       (bookings+restaurant)  Service Windows  (bookings+restaurant)
Class Types  (bookings+gym)  Timetable  (bookings+gym)
Staff        (staff)        CRM  (crm)
Team Chat    (comms)        Health & Safety  (compliance)
Documents    (documents)    Shop  (shop)
Audit Log    (always)       Settings  (always)
```

---

## 8. Known Issues & Bugs

### Critical / High Priority
1. **Shop stock deducted on checkout, not on payment** — If a customer abandons Stripe checkout, stock is still deducted. Needs webhook to reconcile.
2. **No Stripe webhook for shop** — The shop checkout creates orders but doesn't have a webhook to mark orders as `paid` when Stripe payment completes. Orders stay `pending` if using Stripe (currently all demo sites have Stripe key unset so orders auto-mark as `paid`).
3. **Shop image URLs may be relative** — ProductImageSerializer uses `request.build_absolute_uri()` which returns Railway's internal URL. Frontend `getMediaUrl()` helper prepends `NEXT_PUBLIC_API_BASE_URL` for relative paths but if the request context is missing, URLs could be broken.

### Medium Priority
4. **Demo tenant override leaks** — `apiFetch` only applies `_demoTenantSlug` on `/book` pages. The `/shop` page doesn't apply demo tenant override, so it uses `NEXT_PUBLIC_TENANT_SLUG` which is correct for Vercel deployments but won't work for local testing of demo tenants.
5. **Comms polling** — Team chat uses no WebSocket; messages only refresh on manual page reload or interval polling. Real-time updates not implemented.
6. **Frontend `api.ts` hard-coded proxy path** — All calls go to `/api/django`, requiring the Vercel proxy. Direct Railway calls fail due to CORS credential+wildcard issue.
7. **Some debug/diagnostic endpoints still active** — Legacy `/api/v2/` routes and monkey-patch logging in some views should be cleaned up.
8. **`package.json` name still says `nbne-platform-rev2`** — Not updated to rev3.
9. **Django REST Framework `DEFAULT_PERMISSION_CLASSES` is `AllowAny`** — Individual views override this, but any new view without explicit permission classes will be public by default.

### Low Priority
10. **No pagination** — Most list endpoints return all records. Will need pagination for tenants with large datasets.
11. **No image compression** — Uploaded images are stored at original resolution. No server-side thumbnail generation.
12. **No email confirmation for shop orders** — Orders are created but no confirmation email is sent to customers.
13. **`auth.ts` still contains demo user constants** — `authenticateDemoUser()` with hardcoded credentials exists alongside real Django JWT auth.
14. **CSS is all inline styles** — No Tailwind, no CSS modules. Consistent but verbose.

---

## 9. Environment Variables

### Backend (Railway)
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` or `DJANGO_SECRET_KEY` | Yes | insecure dev key | Django secret key |
| `DEBUG` | No | `True` | Debug mode |
| `ALLOWED_HOSTS` | Yes | `localhost,127.0.0.1` | Comma-separated hosts |
| `DATABASE_URL` or `DATABASE_PUBLIC_URL` | Yes | — | PostgreSQL connection |
| `CORS_ALLOWED_ORIGINS` | Yes | localhost + Vercel URLs | Comma-separated origins |
| `CSRF_TRUSTED_ORIGINS` | Yes | Railway + business URLs | Comma-separated origins |
| `STRIPE_SECRET_KEY` | No | `''` | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | No | `''` | Stripe webhook secret |
| `FRONTEND_URL` | No | `http://localhost:3000` | Frontend base URL for Stripe redirects |
| `MEDIA_VOLUME_PATH` | No | `''` | Persistent media volume path |
| `RESEND_API_KEY` | No | `''` | Resend email API key |
| `OPENAI_API_KEY` | No | `''` | OpenAI API key for AI assistant |
| `SEED_TENANT` | No | — | Seed specific tenant on deploy |
| `SEED_ALL_TENANTS` | No | — | Seed all tenants on deploy |
| All `*_MODULE_ENABLED` | No | `True` | Feature flags (9 total) |

### Frontend (Vercel)
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_TENANT_SLUG` | Yes | `''` | Tenant identifier |
| `NEXT_PUBLIC_API_BASE_URL` | No | Railway URL | Backend URL for media URLs |
| `DJANGO_BACKEND_URL` | No | Railway URL | Backend URL for proxy |

---

## 10. Management Commands

| Command | Description |
|---------|-------------|
| `seed_demo [--tenant <slug>] [--delete-demo]` | Seed/reset demo data for tenant(s) |
| `setup_production` | Create default users, services, disclaimers |
| `seed_compliance` | UK HSE baseline compliance items |
| `seed_document_vault` | Default document placeholders |
| `sync_crm_leads` | Sync CRM leads from booking clients |
| `update_demand_index` | Update service demand scoring |
| `backfill_sbe_scores` | Backfill Smart Booking Engine scores |
| `send_booking_reminders [--loop]` | Email reminders (runs as background worker) |

### Startup Sequence (`start.sh`)
1. `migrate --noinput`
2. `collectstatic --noinput`
3. Optional: `seed_demo` (per `SEED_TENANT` / `SEED_ALL_TENANTS`)
4. `seed_demo --tenant nbne` (always)
5. `setup_production`
6. `seed_compliance`
7. `seed_document_vault`
8. `sync_crm_leads`
9. `update_demand_index`
10. `backfill_sbe_scores`
11. `send_booking_reminders --loop` (background)
12. `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --timeout 120`

---

## 11. Testing Approach for Stress Tests

### API Headers Required

For all authenticated requests:
```
Authorization: Bearer <access_token>
X-Tenant-Slug: <tenant-slug>
Content-Type: application/json
```

For multipart uploads:
```
Authorization: Bearer <access_token>
X-Tenant-Slug: <tenant-slug>
(no Content-Type — let the client set multipart boundary)
```

### How to Authenticate via API

```bash
# 1. Get tokens
curl -X POST https://nbneplatform-production.up.railway.app/api/auth/login/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: salon-x" \
  -d '{"username": "owner@demo.local", "password": "admin123"}'

# Response: { "access": "<jwt>", "refresh": "<jwt>", "user": {...} }

# 2. Use the access token
curl https://nbneplatform-production.up.railway.app/api/shop/products/ \
  -H "Authorization: Bearer <access>" \
  -H "X-Tenant-Slug: salon-x"
```

### Recommended Test Flows

**1. Auth Flow**
- Login with each role → verify token → access protected route → verify RBAC enforcement
- Token refresh → verify new token works
- Cross-tenant login rejection (login on salon-x, call with header restaurant-x)
- Invalid credentials → verify 401
- Expired token → verify 401 + refresh flow

**2. Bookings End-to-End (Salon — tenant `salon-x`)**
- List services → select service → get available slots → create booking → confirm → complete
- Cancel booking → verify status change
- Create booking with deposit → verify Stripe redirect (if key set)

**3. Bookings End-to-End (Restaurant — tenant `restaurant-x`)**
- Get available dates → get availability for date+party → create reservation → confirm

**4. Bookings End-to-End (Gym — tenant `health-club-x`)**
- Get class types → get timetable → book class session

**5. Shop End-to-End**
- Admin: create product with metadata → upload images → verify product in list
- Admin: update product price/stock → verify changes
- Admin: delete product image → verify removed
- Admin: reorder images → verify order
- Public: GET public products → verify only active shown
- Public: filter by category
- Public: checkout flow → verify order created with items
- Stock: create product with `track_stock=true`, `stock_quantity=5` → checkout 3 → verify stock=2 → try checkout 4 → verify error

**6. Staff Management**
- Create staff → create shifts → generate timesheets → approve leave
- Working hours CRUD → verify availability engine respects them
- Training records CRUD → verify compliance matrix

**7. Compliance / Health & Safety**
- Create category → create item → assign → complete with evidence (multipart upload)
- Create incident → upload photo → change status → resolve
- Verify dashboard scores update after completion
- Accident book: create → update → delete

**8. Documents**
- Upload document (multipart FormData with `file` field) → list → download → delete
- Tag management: create tag → assign to document
- Expiry tracking: create document with near-future expiry → verify in expiring list

**9. CRM**
- Create lead → update status → add note → view history → convert
- Quick-add from text
- Revenue stats

**10. Team Chat**
- Ensure general channel → send text message → send with file attachment → list messages
- Verify messages scoped to tenant

**11. Multi-Tenant Isolation**
- Create product on tenant A (salon-x) → switch to tenant B (restaurant-x) → verify product not visible
- Login on salon-x → try hitting restaurant-x endpoints with salon-x token but restaurant-x header → verify data isolation
- Verify tenant branding returns correct config per slug

**12. Concurrent Stress**
- Parallel product creation on same tenant
- Parallel checkout for same product (race condition on stock)
- Parallel booking creation for same time slot
- High-frequency polling of dashboard/report endpoints

### Rate Limiting & Concurrency Notes
- **No rate limiting implemented** — all endpoints accept unlimited requests
- Django uses Gunicorn with default worker count (~2-4 on Railway)
- PostgreSQL connection pooling via Railway defaults
- No Redis/cache layer — all queries hit DB directly
- `120s` Gunicorn timeout — long-running operations may timeout
- No database-level locking on stock updates — race conditions possible

---

## 12. File Structure Summary

```
backend/
├── config/           # Django project: settings.py, urls.py, wsgi.py
├── core/             # Auth views, middleware, dashboard, assistant, events
├── accounts/         # Custom User model, RBAC
├── auditlog/         # Request audit trail
├── tenants/          # TenantSettings model, multi-tenant config
├── bookings/         # Full booking system (20+ view files)
├── staff/            # Staff profiles, shifts, leave, training, timesheets
├── comms/            # Team chat channels and messages
├── compliance/       # UK HSE compliance, incidents, RAMS
├── documents/        # Document vault with tagging
├── crm/              # Lead management, notes, history
├── shop/             # Products, images, orders, Stripe checkout
├── payments/         # Stripe integration
├── templates/        # Email templates, admin overrides
├── start.sh          # Railway startup script
└── requirements.txt  # Python dependencies

frontend/
├── app/
│   ├── admin/        # Admin panel (18 sub-pages)
│   ├── app/          # Staff portal
│   ├── api/          # Next.js API routes (Django proxy)
│   ├── book/         # Public booking page
│   ├── shop/         # Public shop + success page
│   ├── salon/        # Salon X landing page
│   ├── restaurant/   # Restaurant X landing page
│   ├── gym/          # Health Club X landing page
│   ├── login/        # Login page
│   └── ...           # Other pages
├── lib/
│   ├── api.ts        # API client (1144 lines, all endpoints)
│   ├── tenant.tsx    # Tenant context provider
│   ├── auth.ts       # JWT utilities
│   ├── types.ts      # TypeScript interfaces
│   └── demo-data.ts  # Demo user data
├── components/       # Shared components (AIChatPanel, FeedbackWidget, DemoBanner)
├── middleware.ts      # Route protection, cache control
└── package.json      # Dependencies
```

---

## 13. Git & Deployment

- **Two remotes:** `origin` → `NBNEORIGIN/nbne_platform` and `vercel` → `NBNEORIGIN/nbne_business`
- **Push to both:** `git push origin dev && git push vercel dev:main && git push origin dev:main`
- **Railway** auto-deploys from `main` branch on `origin`
- **Vercel** auto-deploys from `main` branch on `vercel` remote
- **Demo data resets nightly** (controlled by `SEED_TENANT` / `SEED_ALL_TENANTS`)

---

## 14. Python Dependencies

```
Django>=5.2,<6.0
psycopg2-binary>=2.9,<3.0
python-decouple>=3.8,<4.0
python-dotenv>=1.0,<2.0
whitenoise>=6.6,<7.0
djangorestframework>=3.14,<4.0
djangorestframework-simplejwt>=5.3,<6.0
requests>=2.31,<3.0
django-cors-headers>=4.3,<5.0
gunicorn>=21.2,<22.0
dj-database-url>=2.1,<3.0
django-jazzmin>=2.6,<3.0
Pillow>=10.0,<12.0
stripe>=7.0,<8.0
resend>=0.8.0,<1.0
python-dateutil>=2.8,<3.0
openai>=1.14,<2.0
```

## 15. Frontend Dependencies

```json
{
  "next": "14.2.21",
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "jose": "^5.2.0",
  "bcryptjs": "^2.4.3"
}
```

---

## Version History

| Version | Date | Summary |
|---------|------|---------|
| 3.0.0 | 2026-02-13 | Rev 3 merge: TMD backend + Rev 2 architecture |
| 3.1.0 | 2026-02-25 | Shop module: products, orders, Stripe checkout |
| 3.2.0 | 2026-02-26 | Shop V2: multi-image upload, drag-drop, public shop page, cart, product detail modal |

# NBNE Platform — Stress Test V2 Brief

**Purpose:** Provide enough context for Claude to write a comprehensive second-round stress test script (`nbne_stress_test_v2.py`) that covers all modules, endpoints, and edge cases — including everything added since the first test was written.

---

## 1. Platform Overview

NBNE (product name: **Floe**) is a multi-tenant SaaS platform for small UK service businesses. Each tenant gets a website + full business management backend. The platform is:

- **Backend:** Django 4.2 + DRF, deployed on Railway
- **Frontend:** Next.js 14, deployed on Vercel (one Vercel project per tenant)
- **Database:** PostgreSQL (Railway-managed)
- **File storage:** Cloudflare R2 via django-storages + boto3
- **Payments:** Stripe Checkout (deposits + full payments)
- **Auth:** JWT (access + refresh tokens), custom User model (`accounts.User`)

### Production URLs

| Component | URL |
|---|---|
| Railway backend (main) | `https://nbneplatform-production.up.railway.app` |
| Salon X backend | `https://salon-x-backend-production.up.railway.app` |
| Restaurant X backend | `https://restaurant-x-backend-production.up.railway.app` |
| FitHub backend | `https://health-club-x-backend-production.up.railway.app` |

### Demo Tenants

| Slug | Type | Credentials (owner) |
|---|---|---|
| `salon-x` | Hair/beauty salon | `salon-x-owner` / `admin123` |
| `restaurant-x` | Restaurant | `restaurant-x-owner` / `admin123` |
| `health-club-x` | Gym/fitness | `health-club-x-owner` / `admin123` |
| `nbne` | Internal/generic | `nbne-owner` / `admin123` |

Each tenant also has `-manager` and `-staff1` roles.

### Tenant Resolution

Backend resolves tenant from the `X-Tenant-Slug` HTTP header. All API requests must include this header. The `?tenant=` query param is a belt-and-suspenders fallback.

---

## 2. What V1 Stress Test Already Covers

The existing `nbne_stress_test.py` (743 lines) tests these modules:

| Module | Tests |
|---|---|
| **auth** | Login, /me, invalid creds → 401, cross-tenant token, unauthenticated → 401 |
| **tenant** | GET /api/tenant/branding/ (public) |
| **shop** | Full CRUD product, public list, category filter, checkout, stock deduction, stock exhaustion guard, cleanup |
| **bookings (salon)** | List services, get staff, find available slots (7-day lookahead), create booking, confirm, cancel |
| **bookings (restaurant)** | Available dates, slot availability |
| **bookings (gym)** | Class types, timetable |
| **compliance** | Dashboard, categories, incidents list, create incident |
| **crm** | List leads, create lead, update lead status |
| **staff** | List staff, list leave, list timesheets |
| **documents** | List documents, expiring documents |
| **dashboard** | Today dashboard, reports overview |
| **isolation** | Create product on tenant A → verify not visible on tenant B |
| **concurrent** | 5 simultaneous checkouts for stock=3 product (race condition) |

---

## 3. What V2 Must Add (New Modules & Endpoints Since V1)

### 3.1 CMS Module (`/api/cms/`)

Brand new module added Feb 28. Full CRUD for tenant-editable pages and blog posts.

**Admin endpoints (auth required):**

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/cms/pages/` | List all CMS pages for tenant |
| POST | `/api/cms/pages/create/` | Create a new page |
| GET/PATCH/DELETE | `/api/cms/pages/<id>/` | Page detail / update / delete |
| POST | `/api/cms/pages/<id>/hero/` | Upload hero image (multipart) |
| POST | `/api/cms/pages/<id>/images/` | Upload gallery image (multipart) |
| DELETE | `/api/cms/pages/<id>/images/<img_id>/` | Delete gallery image |
| GET | `/api/cms/blog/` | List all blog posts for tenant |
| POST | `/api/cms/blog/create/` | Create blog post |
| GET/PATCH/DELETE | `/api/cms/blog/<id>/` | Blog post detail / update / delete |
| POST | `/api/cms/blog/<id>/image/` | Upload featured image (multipart) |

**Public endpoints (no auth):**

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/cms/public/pages/` | Published pages |
| GET | `/api/cms/public/pages/<slug>/` | Single published page by slug |
| GET | `/api/cms/public/blog/` | Published blog posts |
| GET | `/api/cms/public/blog/<slug>/` | Single published blog post by slug |

**V2 test plan:** Full lifecycle — create page with fields (title, slug, content, hero_headline, is_published, show_in_nav, meta_title, meta_description), update, verify in public list when published, verify NOT in public list when unpublished, upload hero image, upload gallery images, delete gallery image, delete page. Same for blog posts (title, slug, excerpt, content, author_name, category, tags, status=draft/published, published_at). Test tenant isolation (page on tenant A not visible on tenant B public endpoint).

### 3.2 Enhanced Service Descriptions

Services now have `long_description` (rich text HTML) and `brochure` (file upload) fields.

**New endpoints:**

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/services/<id>/upload_brochure/` | Upload brochure file (multipart) |
| DELETE | `/api/services/<id>/delete_brochure/` | Remove brochure |

**V2 test plan:** Create a service, update it with `long_description` containing HTML, verify it round-trips. Upload a brochure file, verify `brochure_url` and `brochure_filename` are returned. Delete brochure, verify fields are null. Verify `long_description` appears in service detail response.

### 3.3 Dynamic Categories

Documents, services, and shop products now use free-text categories instead of hardcoded choices.

**New endpoint:**

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/documents/categories/` | Returns list of categories used by this tenant's documents |

**V2 test plan:** Create documents with different categories, then hit `/api/documents/categories/` and verify they appear. Verify categories are tenant-scoped (tenant A's categories don't appear on tenant B).

### 3.4 Comms Module (`/api/comms/`)

Team messaging — internal channels and messages.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/comms/channels/` | List channels |
| GET | `/api/comms/channels/<id>/messages/` | List messages in channel |
| POST | `/api/comms/channels/<id>/messages/create/` | Send a message |
| POST | `/api/comms/ensure-general/` | Create/get the default "General" channel |

**V2 test plan:** Ensure general channel, list channels, send a message, verify it appears in message list. Test that messages from tenant A's channel are not visible on tenant B.

### 3.5 Staff Module — Deeper Coverage (`/api/staff-module/`)

V1 only tested list staff, leave, timesheets. V2 should cover:

| Area | Endpoints to test |
|---|---|
| **Shifts** | CRUD: `/shifts/`, `/shifts/create/`, `/shifts/<id>/update/`, `/shifts/<id>/delete/` |
| **Leave** | Create, review (approve/deny), delete, calendar view |
| **Training** | List, create, delete, courses CRUD, compliance status, reminders |
| **Working Hours** | List, create, bulk-set, update, delete |
| **Timesheets** | List, generate, summary, update, export CSV |
| **Project Codes** | CRUD: list, create, update, delete |
| **Payroll** | `GET /payroll/summary/?month=YYYY-MM` |
| **Hours Tally** | `GET /hours-tally/` |
| **Leave Balance** | `GET /leave-balance/` |
| **Quick Time Log** | `POST /timesheets/quick-log/` |

### 3.6 CRM Module — Deeper Coverage (`/api/crm/`)

V1 only tested list leads, create lead, update status. V2 should cover:

| Area | Endpoints to test |
|---|---|
| **Lead actions** | `/leads/<id>/contact/`, `/leads/<id>/convert/`, `/leads/<id>/followup-done/` |
| **Lead notes** | `GET/POST /leads/<id>/notes/` |
| **Lead history** | `GET /leads/<id>/history/` |
| **Lead revenue** | `GET /leads/<id>/revenue/` |
| **Revenue stats** | `GET /revenue/` |
| **CSV export** | `GET /leads/export/` |
| **Quick add** | `POST /leads/quick-add/` |
| **Sync** | `POST /sync/` (sync leads from bookings) |

### 3.7 Shop Module — Deeper Coverage (`/api/shop/`)

V1 tested basic CRUD + checkout. V2 should add:

| Area | Endpoints to test |
|---|---|
| **Product images** | Upload: `POST /products/<id>/images/`, Delete: `DELETE /products/<id>/images/<img_id>/`, Reorder: `POST /products/<id>/images/reorder/` |
| **Order management** | List orders: `GET /orders/`, order detail, status updates |

### 3.8 Compliance Module — Deeper Coverage (`/api/compliance/`)

V1 tested dashboard, categories, incidents. V2 should add:

| Area | Endpoints |
|---|---|
| **Items** | CRUD for compliance items (register) |
| **Training records** | List, create training records |
| **Document vault** | Upload, list, version tracking |
| **Calendar** | `GET /calendar/` |
| **CSV export** | `GET /export/` |
| **My actions** | `GET /my-actions/` |
| **My training** | `GET /my-training/` |

### 3.9 Reports Module (Deeper)

| Endpoint | Purpose |
|---|---|
| `GET /api/reports/daily/` | Daily report |
| `GET /api/reports/monthly/` | Monthly report |
| `GET /api/reports/staff/` | Staff performance |
| `GET /api/reports/insights/` | Business insights |
| `GET /api/reports/staff-hours/` | Staff hours summary |
| `GET /api/reports/staff-hours/csv/` | CSV export |
| `GET /api/reports/leave/` | Leave report |

### 3.10 Public/Unauthenticated Endpoints

These should be tested WITHOUT auth to verify they work for anonymous visitors:

| Endpoint | Purpose |
|---|---|
| `GET /api/tenant/branding/` | Tenant branding/config |
| `GET /api/shop/public/products/` | Public product listing |
| `GET /api/cms/public/pages/` | Public CMS pages |
| `GET /api/cms/public/blog/` | Public blog posts |
| `POST /api/contact/` | Contact form submission |
| `POST /api/beta-signup/` | Beta signup |
| `GET /api/gym-class-types/` | Gym class types |
| `GET /api/gym-timetable/` | Gym timetable |
| `GET /api/restaurant-availability/` | Restaurant availability |
| `GET /api/restaurant-available-dates/` | Restaurant available dates |
| `GET /api/bookings/slots/` | Booking slot availability |
| `POST /api/bookings/create/` | Public booking creation |

### 3.11 AI Assistant

| Endpoint | Purpose |
|---|---|
| `POST /api/assistant/chat/` | AI chat (requires auth + OpenAI key on backend) |

**V2 test plan:** Send a simple message, verify 200 response (may get degraded response if no OpenAI key). Test that unauthenticated request returns 401.

### 3.12 Availability Engine

| Endpoint | Purpose |
|---|---|
| `GET /api/availability/?staff_id=X&date=YYYY-MM-DD` | Staff availability for a date |
| `GET /api/availability/slots/?staff_id=X&date=YYYY-MM-DD&duration=60` | Free slots |
| DRF router: `working-patterns`, `working-pattern-rules`, `availability-overrides`, `leave-requests`, `blocked-times`, `shifts`, `timesheets` | CRUD via standard DRF viewsets |

---

## 4. V2 Test Architecture Requirements

### 4.1 Keep V1 Pattern

- Same `Result` dataclass, `record()` function, `api()` helper, `login()` helper
- Same argparse CLI with `--modules` and `--tenant` flags
- Same summary output with pass/fail counts and performance metrics
- Keep `X-Tenant-Slug` header on all requests

### 4.2 New Capabilities Needed

- **File upload tests:** The `api()` helper already supports `files=` param. Use it for CMS hero/gallery images, blog featured images, service brochures, and shop product images. Create small in-memory test images (1x1 PNG or similar).
- **CSV download tests:** Verify endpoints that return `text/csv` (timesheets export, CRM export, compliance export, staff hours CSV). Check `Content-Type` header and that body is non-empty.
- **Lifecycle tests:** For CMS and blog, test the full create → update → publish → verify public → unpublish → verify gone from public → delete lifecycle.
- **Permission tests:** Test that staff-role users cannot access owner-only endpoints (e.g., delete product, delete staff member). Test that unauthenticated users get 401 on protected endpoints.
- **Rate limit tests:** The contact form is rate-limited to 5/hour. Test that the 6th submission within a short window returns 429.
- **Idempotency tests:** Creating the same resource twice (e.g., same slug for CMS page) should return an appropriate error, not create duplicates.

### 4.3 Cleanup

All test data created during the run must be cleaned up (deleted) at the end of each test function. Use unique tags (UUID prefix) so test data is identifiable. If deletion fails, log a warning but don't fail the test.

### 4.4 Module Map

```python
MODULE_MAP = {
    "auth":         ...,
    "tenant":       ...,
    "shop":         ...,  # expanded with image upload, order management
    "bookings":     ...,  # salon, restaurant, gym variants
    "compliance":   ...,  # expanded with items, training, vault, calendar
    "crm":          ...,  # expanded with actions, notes, history, revenue, export
    "staff":        ...,  # expanded with shifts, leave CRUD, training, working hours, timesheets, project codes, payroll
    "documents":    ...,  # expanded with categories, create/delete lifecycle
    "dashboard":    ...,  # expanded with all report endpoints
    "cms":          ...,  # NEW: full lifecycle for pages and blog posts
    "comms":        ...,  # NEW: channels and messages
    "services":     ...,  # NEW: long_description + brochure upload/delete
    "public":       ...,  # NEW: all unauthenticated endpoints
    "permissions":  ...,  # NEW: role-based access control checks
    "isolation":    ...,  # expanded: CMS, blog, comms isolation
    "concurrent":   ...,  # keep existing stock race test
    "assistant":    ...,  # NEW: AI assistant endpoint
}
```

---

## 5. Edge Cases to Cover

1. **Empty tenant:** Request with no `X-Tenant-Slug` header — should get a sensible error, not crash
2. **Invalid tenant slug:** Request with `X-Tenant-Slug: nonexistent-tenant` — should 404 or 400
3. **Expired JWT:** Use a mangled/expired token — should 401
4. **Large payload:** Create a CMS page with very long `content` field (10KB+ of HTML)
5. **Special characters:** Create a blog post with title containing `"Café & Bar — O'Brien's"` — verify slug generation handles unicode/special chars
6. **Duplicate slug:** Create two CMS pages with the same title — second should either auto-suffix or error (unique_together constraint)
7. **Zero-quantity checkout:** Attempt checkout with `quantity: 0` — should be rejected
8. **Negative price:** Attempt to create product with `price: "-5.00"` — should be rejected
9. **SQL injection in search/filter:** Pass `'; DROP TABLE--` as category filter — should not crash
10. **XSS in text fields:** Store `<script>alert('xss')</script>` in a field — verify it's stored but doesn't execute (content-type should be application/json)
11. **Booking in the past:** Attempt to create a booking for yesterday — should be rejected
12. **Double-booking:** Book same slot twice — second should fail or handle gracefully
13. **File upload limits:** Upload a very large file (or file with wrong extension) to brochure endpoint — verify appropriate error

---

## 6. Expected Output Format

Same as V1:

```
NBNE Wiggum Stress Test V2
Backend: https://nbneplatform-production.up.railway.app
Modules: auth, tenant, shop, bookings, ...
Tenants: salon-x, restaurant-x, health-club-x, nbne
Started: 2026-02-28 14:00:00

── AUTH [salon-x] ──
  ✅ [salon-x] Owner login returns JWT (200) [312ms]
  ✅ [salon-x] GET /api/auth/me/ returns 200 (200) [198ms]
  ...

═══════════════════════════════════════════════════
STRESS TEST V2 SUMMARY
═══════════════════════════════════════════════════
  Total:  187
  Passed: 183 ✅
  Failed: 4 ❌

FAILURES:
  ❌ [cms] [salon-x] Duplicate slug returns error (500) — Expected 400, got 500
  ...

PERFORMANCE:
  Average response: 245ms
  Slow requests (>3s):
    [shop] Checkout with Stripe: 4200ms
═══════════════════════════════════════════════════
```

---

## 7. How to Run

```bash
pip install requests
python nbne_stress_test_v2.py                          # all modules, all tenants
python nbne_stress_test_v2.py --modules cms blog        # specific modules
python nbne_stress_test_v2.py --tenant salon-x          # specific tenant
python nbne_stress_test_v2.py --modules public          # public endpoints only
python nbne_stress_test_v2.py --modules permissions     # permission checks only
```

---

## 8. File Location

Output to: `d:\nbne_business\revisions\nbne_business_rev_3\nbne_stress_test_v2.py`

Keep V1 (`nbne_stress_test.py`) intact — V2 is a separate, more comprehensive file.

# NBNE Business Platform — Fresh Instance Deployment Guide

> **Version:** Rev 3 | **Last updated:** February 2026
> **Author:** NBNE Engineering

This document walks through deploying a brand-new client instance of the NBNE Business Platform from scratch. It covers everything: Railway backend, Vercel frontend, database seeding, storage, email, payments, DNS, and post-launch verification.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Architecture Overview](#2-architecture-overview)
3. [Step 1: Create the Railway Backend](#3-step-1-create-the-railway-backend)
4. [Step 2: Configure Railway Environment Variables](#4-step-2-configure-railway-environment-variables)
5. [Step 3: Seed the Database](#5-step-3-seed-the-database)
6. [Step 4: Create the Vercel Frontend](#6-step-4-create-the-vercel-frontend)
7. [Step 5: Configure Vercel Environment Variables](#7-step-5-configure-vercel-environment-variables)
8. [Step 6: Wire Up CORS](#8-step-6-wire-up-cors)
9. [Step 7: Custom Domain (Optional)](#9-step-7-custom-domain-optional)
10. [Step 8: Verify Everything Works](#10-step-8-verify-everything-works)
11. [Automated Deployment Script](#11-automated-deployment-script)
12. [Adding a New Tenant to Seed Data](#12-adding-a-new-tenant-to-seed-data)
13. [Environment Variable Reference](#13-environment-variable-reference)
14. [Troubleshooting](#14-troubleshooting)
15. [Live Instances Reference](#15-live-instances-reference)
16. [Security Notes](#16-security-notes)

---

## 1. Prerequisites

Before you begin, ensure you have:

- **Railway CLI** installed and authenticated (`railway login`)
- **Vercel account** with access to the NBNE team
- **GitHub access** to `NBNEORIGIN/nbne_platform` (private repo)
- **Python 3.11+** installed locally (for running management commands)
- **Node.js 18+** installed locally (for local frontend dev)
- **Cloudflare R2** credentials (for document/media storage)
- **Stripe** account and API keys (if payments are needed)
- **IONOS SMTP** credentials (for transactional email)

### Tools

| Tool | Install | Purpose |
|------|---------|---------|
| Railway CLI | `npm i -g @railway/cli` | Backend deployment |
| Vercel CLI | `npm i -g vercel` | Frontend deployment (optional, dashboard works too) |
| Git | Standard | Source control |
| Python 3.11+ | python.org | Running Django management commands locally |

---

## 2. Architecture Overview

Each client gets **its own isolated stack** to prevent data cross-contamination:

```
  Vercel (Frontend)                    Railway (Backend)
  +--------------------------+         +--------------------------+
  | Next.js 14 (App Router)  |-------->| Django 5.2 + DRF         |
  | React 18 + TypeScript    |         | PostgreSQL               |
  | NEXT_PUBLIC_TENANT_SLUG  |         | Gunicorn + WhiteNoise    |
  +--------------------------+         | Cloudflare R2 (media)    |
                                       +--------------------------+
```

**Per-client isolation:**
- 1 Railway project (backend service + Postgres addon)
- 1 Vercel project (same codebase, different env vars)
- Tenant slug determines which data is served
- `SEED_TENANT` env var controls which demo data is seeded on deploy

**Shared resources:**
- GitHub repo: `NBNEORIGIN/nbne_platform`
- Cloudflare R2 bucket: `documents` (shared, files are tenant-prefixed)
- IONOS SMTP: `toby@nbnesigns.com` (can be overridden per client)

---

## 3. Step 1: Create the Railway Backend

### Option A: Automated (recommended)

```powershell
cd D:\nbne_business\revisions\nbne_business_rev_3
.\scripts\deploy_client.ps1 -ClientName "My Salon" -TenantSlug "my-salon"
```

This creates the Railway project, Postgres, backend service, sets env vars, runs migrations, and seeds data. Skip to Step 4 if using this.

### Option B: Manual

#### 3.1 Create Railway project

```bash
railway init --name nbne-my-salon
```

#### 3.2 Add Postgres

```bash
railway add -d postgres
```

Wait around 10 seconds for provisioning.

#### 3.3 Add backend service from GitHub

```bash
railway add -s my-salon-backend -r NBNEORIGIN/nbne_platform
```

#### 3.4 Link to the backend service

```bash
railway link -p nbne-my-salon -s my-salon-backend
```

#### 3.5 Generate a public domain

```bash
railway domain -s my-salon-backend
```

This gives you a URL like `my-salon-backend-production.up.railway.app`. Note this down for Vercel config.

#### 3.6 Set the root directory

The repo has both `backend/` and `frontend/` at the root. Railway must only build the backend:

```bash
railway variable set "RAILWAY_ROOT_DIRECTORY=backend"
```

**CRITICAL:** Without this, Railway tries to build the entire repo and fails. This was a common issue with Tavola and FitHub deployments.

---

## 4. Step 2: Configure Railway Environment Variables

Set all required env vars. Replace placeholders with real values.

### 4.1 Core Django

```bash
railway variable set "DJANGO_SECRET_KEY=GENERATE_A_RANDOM_50_CHAR_STRING" "DEBUG=False" "ALLOWED_HOSTS=.up.railway.app,localhost,127.0.0.1" "RAILWAY_ROOT_DIRECTORY=backend"
```

Generate a secret key with:
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 4.2 Module flags

All modules enabled by default. Disable any that are not needed:

```bash
railway variable set "BOOKINGS_MODULE_ENABLED=True" "PAYMENTS_MODULE_ENABLED=True" "STAFF_MODULE_ENABLED=True" "COMMS_MODULE_ENABLED=True" "COMPLIANCE_MODULE_ENABLED=True" "DOCUMENTS_MODULE_ENABLED=True" "CRM_MODULE_ENABLED=True" "ANALYTICS_MODULE_ENABLED=True" "TENANTS_MODULE_ENABLED=True"
```

### 4.3 Tenant seeding

```bash
railway variable set "SEED_TENANT=my-salon"
```

This tells `start.sh` to delete and re-seed this tenant's demo data on every deploy. **Remove this var for live/production clients** where you do not want data reset.

### 4.4 Email (IONOS SMTP)

```bash
railway variable set "EMAIL_HOST=smtp.ionos.co.uk" "EMAIL_PORT=587" "EMAIL_HOST_USER=toby@nbnesigns.com" "EMAIL_HOST_PASSWORD=!49Monkswood" "DEFAULT_FROM_EMAIL=toby@nbnesigns.com" "EMAIL_BRAND_NAME=My Salon" "REMINDER_EMAIL_HOST=smtp.ionos.co.uk" "REMINDER_EMAIL_PORT=465" "REMINDER_EMAIL_USE_SSL=True" "REMINDER_EMAIL_HOST_USER=toby@nbnesigns.com" "REMINDER_EMAIL_HOST_PASSWORD=!49Monkswood" "REMINDER_FROM_EMAIL=toby@nbnesigns.com"
```

For production clients, set up a dedicated email address (e.g. `noreply@clientdomain.com`).

### 4.5 Cloudflare R2 Storage

```bash
railway variable set "R2_ACCESS_KEY_ID=H0GXfvz29XtAbmaJSjfqehm5AfYVig6XAHbWNPWD" "R2_SECRET_ACCESS_KEY=65e1a0f773a40de988a66379f9db0cb43937c417145f4a673257f12d56f61bd9" "R2_ENDPOINT_URL=https://5551fa1ba3cec479fd938b41b642e9.r2.cloudflarestorage.com" "R2_PUBLIC_URL=https://pub-0a37d1fed9c043aab8f7180d8b112489.r2.dev"
```

Without R2, document uploads and media files will only persist until the next Railway deploy (ephemeral filesystem).

### 4.6 Stripe Payments (optional)

```bash
railway variable set "STRIPE_SECRET_KEY=sk_test_..." "STRIPE_WEBHOOK_SECRET=whsec_..."
```

### 4.7 CORS

Leave this for now. You will come back to set it once you have the Vercel URL (Step 6).

---

## 5. Step 3: Seed the Database

### Automatic (on deploy)

If `SEED_TENANT=my-salon` is set, `start.sh` automatically runs:

1. `python manage.py migrate --noinput`
2. `python manage.py seed_demo --tenant my-salon --delete-demo`
3. `python manage.py seed_demo --tenant my-salon`
4. `python manage.py seed_compliance`
5. `python manage.py seed_document_vault`
6. Various other setup commands

### Manual (via Railway CLI)

```bash
railway run python manage.py migrate --noinput
railway run python manage.py seed_demo --tenant my-salon
railway run python manage.py seed_compliance
railway run python manage.py seed_document_vault
```

### Existing tenant slugs in seed data

| Slug | Business Name | Type | Notes |
|------|--------------|------|-------|
| `salon-x` | Salon X | `salon` | Demo hairdresser |
| `restaurant-x` | Tavola | `restaurant` | Demo restaurant with 10 tables, 12 service windows |
| `health-club-x` | FitHub | `gym` | Demo gym with 6 class types, 27 sessions |
| `mind-department` | The Mind Department | `generic` | **LIVE CLIENT. DO NOT SEED OR DELETE.** |
| `nbne` | NBNE | `generic` | Internal NBNE instance with real staff |

**WARNING:** Never run `seed_demo` without `--tenant` on a production backend. The default run excludes `mind-department` (protected in `LIVE_TENANTS` set), but always be explicit.

### Demo login credentials

After seeding, these users are created:

| Username | Email | Password | Role |
|----------|-------|----------|------|
| `{slug}-owner` | `owner@{slug}.demo` | `admin123` | Owner |
| `{slug}-manager` | `manager@{slug}.demo` | `admin123` | Manager |
| `{slug}-staff1` | `staff1@{slug}.demo` | `admin123` | Staff |
| `{slug}-staff2` | `staff2@{slug}.demo` | `admin123` | Staff |
| `{slug}-customer` | `customer@{slug}.demo` | `admin123` | Customer |

Tenants with `staff_users` config (e.g. `nbne`) create named users instead:

| Username | Email | Password | Role |
|----------|-------|----------|------|
| `toby` | `toby@nbnesigns.com` | `admin123` | Owner |
| `jo` | `jo@nbnesigns.com` | `admin123` | Manager |

---

## 6. Step 4: Create the Vercel Frontend

### Via Vercel Dashboard (recommended)

1. Go to vercel.com/new
2. Import from GitHub: `NBNEORIGIN/nbne_business`
3. **Root Directory:** `frontend`
4. **Framework Preset:** Next.js
5. **Build Command:** `next build` (default)
6. **Output Directory:** `.next` (default)
7. Set environment variables (see Step 5)
8. Deploy

---

## 7. Step 5: Configure Vercel Environment Variables

Set these in the Vercel project settings under Environment Variables:

| Variable | Value | Required |
|----------|-------|----------|
| `NEXT_PUBLIC_TENANT_SLUG` | `my-salon` | Yes |
| `NEXT_PUBLIC_API_BASE_URL` | `https://my-salon-backend-production.up.railway.app` | Yes |
| `DJANGO_BACKEND_URL` | `https://my-salon-backend-production.up.railway.app` | Yes |

### What each variable does

- **`NEXT_PUBLIC_TENANT_SLUG`** identifies which tenant this frontend serves. Used at build time to determine the homepage (salon/restaurant/gym landing, or redirect to admin). Also sent as `X-Tenant-Slug` header on every API call.
- **`NEXT_PUBLIC_API_BASE_URL`** is used client-side for media URLs and as a fallback API base. Must be the full Railway backend URL with `https://`.
- **`DJANGO_BACKEND_URL`** is used server-side by the Next.js API proxy route (`/api/django/[...path]`). This is the actual URL that API requests are forwarded to.

**Common mistake:** Setting these to the shared `nbneplatform-production.up.railway.app` instead of the client-specific backend. Each client must point to their own Railway backend for data isolation.

After setting env vars, **redeploy** the Vercel project. `NEXT_PUBLIC_*` vars are baked in at build time.

---

## 8. Step 6: Wire Up CORS

Now that you have the Vercel URL (e.g. `my-salon-abc.vercel.app`), go back to Railway:

```bash
railway link -p nbne-my-salon -s my-salon-backend
railway variable set "CORS_ALLOWED_ORIGINS=https://my-salon-abc.vercel.app,https://localhost:3000" "CSRF_TRUSTED_ORIGINS=https://my-salon-abc.vercel.app,https://my-salon-backend-production.up.railway.app"
```

If the client has a custom domain, add it too:

```bash
railway variable set "CORS_ALLOWED_ORIGINS=https://my-salon-abc.vercel.app,https://app.mysalon.com,https://localhost:3000" "CSRF_TRUSTED_ORIGINS=https://my-salon-abc.vercel.app,https://app.mysalon.com,https://my-salon-backend-production.up.railway.app"
```

Without CORS, the frontend will get `403 Forbidden` on every API call. This is the number one cause of "blank page" or "Business" showing as the name.

---

## 9. Step 7: Custom Domain (Optional)

### Vercel (frontend)

1. Vercel dashboard, Project, Settings, Domains
2. Add domain: `app.mysalon.com`
3. Set DNS: CNAME `app` pointing to `cname.vercel-dns.com`

### Railway (backend API, usually not needed)

Only needed if the client wants a branded API URL. The default `*.up.railway.app` domain works fine.

### DNS Records

| Type | Name | Value | Purpose |
|------|------|-------|---------|
| CNAME | `app` | `cname.vercel-dns.com` | Frontend |
| CNAME | `api` (optional) | `my-salon-backend-production.up.railway.app` | Backend API |

---

## 10. Step 8: Verify Everything Works

### 10.1 Backend health check

```bash
curl https://my-salon-backend-production.up.railway.app/api/tenant/branding/?tenant=my-salon
```

Expected: JSON response with `business_name`, `business_type`, `colour_primary`, etc.

If you get a 500 or empty response, check Railway deploy logs, verify `SEED_TENANT` is set, and run the seed manually if needed.

### 10.2 Frontend loads branding

Visit the Vercel URL. You should see the correct business name, brand colours, and no "Business" placeholder text.

If you see "Business" as the name:
- `NEXT_PUBLIC_TENANT_SLUG` is wrong or missing on Vercel
- `DJANGO_BACKEND_URL` is wrong (pointing to wrong Railway backend)
- CORS is blocking the branding API call (check browser console)

### 10.3 Login works

1. Go to `/login`
2. Enter demo credentials: `owner@my-salon.demo` / `admin123`
3. Should redirect to `/admin` dashboard

### 10.4 Booking flow

Visit `/book`. Depending on `business_type`:
- **salon**: Service, Staff, Date, Time, Details
- **restaurant**: Party Size, Date, Time Window, Details
- **gym**: Weekly Timetable, Pick Class, Details

### 10.5 Admin panel

After login, check:
- Dashboard loads with stats
- Sidebar shows correct modules
- Restaurant tenants see "Tables" and "Service Windows"
- Gym tenants see "Class Types" and "Timetable"
- No "This is a demo" banner for live clients

---

## 11. Automated Deployment Script

The PowerShell script at `scripts/deploy_client.ps1` automates steps 1 through 3:

```powershell
.\scripts\deploy_client.ps1 -ClientName "Salon X" -TenantSlug "salon-x"
```

### What it does

1. Creates Railway project `nbne-salon-x`
2. Adds Postgres addon
3. Adds backend service from GitHub
4. Sets all env vars (Django, modules, email, Stripe)
5. Generates Railway domain
6. Triggers deployment
7. Runs migrations
8. Seeds demo data

### What it does NOT do

- Create the Vercel project (manual, Step 4)
- Set Vercel env vars (manual, Step 5)
- Configure CORS (manual, Step 6)
- Set up R2 storage (manual, Step 4.5)
- Set up custom domains (manual, Step 7)

---

## 12. Adding a New Tenant to Seed Data

To add a new tenant to the seed system, edit `backend/accounts/management/commands/seed_demo.py`.

### 12.1 Add to TENANTS dict

```python
'my-salon': {
    'business_type': 'salon',          # salon | restaurant | gym | generic
    'business_name': 'My Salon',
    'tagline': 'Your tagline here',
    'colour_primary': '#2563eb',
    'colour_secondary': '#1e40af',
    'email': 'hello@mysalon.com',
    'phone': '07700 900000',
    'address': 'London, UK',
    'deposit_percentage': 25,
    'booking_staff_label': 'Stylist',
    'booking_staff_label_plural': 'Stylists',
    'enabled_modules': [
        'bookings', 'payments', 'staff', 'comms',
        'compliance', 'documents', 'crm', 'analytics',
    ],
    'services': [
        # (name, category, duration_mins, price_str, deposit_pence)
        ('Cut and Blow Dry', 'Hair', 45, '35.00', 1000),
        ('Colour', 'Hair', 90, '75.00', 2000),
    ],
    'booking_staff': [
        # (email, display_name, role, [service_names], break_start, break_end)
        ('stylist1@mysalon.com', 'Jane Doe', 'staff',
         ['Cut and Blow Dry', 'Colour'], '12:00', '12:30'),
    ],
    'demo_clients': [
        # (name, email, phone)
        ('Alice Smith', 'alice@example.com', '07700 900001'),
    ],
    'comms_channels': [('General', 'GENERAL'), ('Team', 'TEAM')],
},
```

### 12.2 Restaurant-specific fields

```python
'tables': [
    # (name, min_seats, max_seats, zone, is_combinable)
    ('Table 1', 2, 2, 'Main', False),
    ('Table 2', 4, 4, 'Main', True),
],
'service_windows': [
    # (name, day, open_time, close_time, last_booking, turn_mins, max_covers)
    ('Lunch', 0, '12:00', '14:30', '14:00', 90, 40),
    ('Dinner', 0, '18:00', '22:00', '21:00', 120, 60),
],
```

### 12.3 Gym-specific fields

```python
'class_types': [
    # (name, category, duration_mins, difficulty, max_capacity, colour, price_pence)
    ('Yoga Flow', 'Mind and Body', 60, 'beginner', 20, '#10b981', 1200),
    ('HIIT', 'Cardio', 45, 'advanced', 25, '#ef4444', 1500),
],
'class_sessions': [
    # (class_type_name, instructor_name, day_of_week, start, end, room, cap_override)
    ('Yoga Flow', 'Jane Doe', 0, '09:00', '10:00', 'Studio 1', None),
    ('HIIT', 'John Smith', 1, '18:00', '18:45', 'Main Hall', 30),
],
```

### 12.4 Named staff users (for live clients)

```python
'staff_users': [
    # (username, email, first_name, last_name, role)
    ('jane', 'jane@mysalon.com', 'Jane', 'Doe', 'owner'),
    ('john', 'john@mysalon.com', 'John', 'Smith', 'manager'),
],
```

### 12.5 Protecting live clients

Add the slug to the `LIVE_TENANTS` set to prevent accidental seeding:

```python
LIVE_TENANTS = {'mind-department', 'my-salon'}
```

---

## 13. Environment Variable Reference

### Railway Backend: Required

| Variable | Example | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | `abc123...` | Random 50+ char string. Must be unique per instance. |
| `DEBUG` | `False` | Always `False` in production |
| `ALLOWED_HOSTS` | `.up.railway.app,localhost` | Comma-separated allowed hosts |
| `DATABASE_URL` | `postgresql://...` | Auto-set by Railway Postgres addon |
| `RAILWAY_ROOT_DIRECTORY` | `backend` | CRITICAL. Tells Railway to build from backend/ subdirectory |
| `SEED_TENANT` | `my-salon` | Tenant slug to seed on every deploy. Remove for live clients. |
| `CORS_ALLOWED_ORIGINS` | `https://my-app.vercel.app` | Comma-separated Vercel URLs |
| `CSRF_TRUSTED_ORIGINS` | `https://my-app.vercel.app` | Same as CORS plus Railway URL |

### Railway Backend: Module Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `BOOKINGS_MODULE_ENABLED` | `True` | Booking engine |
| `PAYMENTS_MODULE_ENABLED` | `True` | Stripe payments |
| `STAFF_MODULE_ENABLED` | `True` | HR and staff management |
| `COMMS_MODULE_ENABLED` | `True` | Team chat |
| `COMPLIANCE_MODULE_ENABLED` | `True` | Health and safety |
| `DOCUMENTS_MODULE_ENABLED` | `True` | Document vault |
| `CRM_MODULE_ENABLED` | `True` | Lead management |
| `ANALYTICS_MODULE_ENABLED` | `True` | Analytics dashboard |
| `TENANTS_MODULE_ENABLED` | `True` | Tenant settings API |

### Railway Backend: Storage (Cloudflare R2)

| Variable | Value |
|----------|-------|
| `R2_ACCESS_KEY_ID` | `H0GXfvz29XtAbmaJSjfqehm5AfYVig6XAHbWNPWD` |
| `R2_SECRET_ACCESS_KEY` | `65e1a0f773a40de988a66379f9db0cb43937c417145f4a673257f12d56f61bd9` |
| `R2_ENDPOINT_URL` | `https://5551fa1ba3cec479fd938b41b642e9.r2.cloudflarestorage.com` |
| `R2_PUBLIC_URL` | `https://pub-0a37d1fed9c043aab8f7180d8b112489.r2.dev` |

Without these, media uploads use Railway ephemeral filesystem and are lost on redeploy.

### Railway Backend: Email (IONOS SMTP)

| Variable | Value |
|----------|-------|
| `EMAIL_HOST` | `smtp.ionos.co.uk` |
| `EMAIL_PORT` | `587` |
| `EMAIL_HOST_USER` | `toby@nbnesigns.com` |
| `EMAIL_HOST_PASSWORD` | `!49Monkswood` |
| `DEFAULT_FROM_EMAIL` | `toby@nbnesigns.com` |
| `REMINDER_EMAIL_HOST` | `smtp.ionos.co.uk` |
| `REMINDER_EMAIL_PORT` | `465` |
| `REMINDER_EMAIL_USE_SSL` | `True` |
| `REMINDER_EMAIL_HOST_USER` | `toby@nbnesigns.com` |
| `REMINDER_EMAIL_HOST_PASSWORD` | `!49Monkswood` |
| `REMINDER_FROM_EMAIL` | `toby@nbnesigns.com` |

### Railway Backend: Payments (Stripe)

| Variable | Example | Description |
|----------|---------|-------------|
| `STRIPE_SECRET_KEY` | `sk_test_...` | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` | Stripe webhook signing secret |

### Vercel Frontend: Required

| Variable | Example | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_TENANT_SLUG` | `my-salon` | Must match the tenant slug in the database |
| `NEXT_PUBLIC_API_BASE_URL` | `https://my-salon-backend-production.up.railway.app` | Railway backend URL |
| `DJANGO_BACKEND_URL` | `https://my-salon-backend-production.up.railway.app` | Same as above (used server-side by API proxy) |

---

## 14. Troubleshooting

### Frontend shows "Business" as the name

**Cause:** Branding API call failed.

**Fix:**
1. Check `NEXT_PUBLIC_TENANT_SLUG` is set correctly in Vercel
2. Check `DJANGO_BACKEND_URL` points to the correct per-client Railway backend
3. Check CORS is configured on Railway to allow the Vercel domain
4. Check Railway deploy logs for errors
5. Test the branding endpoint directly: `curl https://BACKEND_URL/api/tenant/branding/?tenant=SLUG`

### Login returns 403 or fails silently

**Cause:** CORS blocking the request.

**Fix:**
1. Open browser dev tools, check Console for CORS errors
2. Ensure `CORS_ALLOWED_ORIGINS` on Railway includes the exact Vercel URL (with `https://`)
3. Ensure `CSRF_TRUSTED_ORIGINS` on Railway includes both the Vercel URL and the Railway URL
4. Redeploy Railway after changing env vars

### Railway build fails

**Cause:** Root directory not set.

**Fix:**
```bash
railway variable set "RAILWAY_ROOT_DIRECTORY=backend"
```

The repo contains both `backend/` and `frontend/`. Without this variable, Railway tries to detect the framework from the repo root and fails.

### Booking flow shows wrong type (e.g. salon flow on a restaurant)

**Cause:** `business_type` not set on the tenant in the database.

**Fix:**
```bash
railway run python manage.py seed_demo --tenant SLUG
```

This runs `update_or_create` on the TenantSettings, setting the correct `business_type` from the seed data.

### Demo banner shows on a live client

**Cause:** The `nbne` slug check in the admin layout.

**Fix:** The demo banner only hides for `NEXT_PUBLIC_TENANT_SLUG=nbne`. For other live clients, add their slug to the check in `frontend/app/admin/layout.tsx`:

```typescript
const LIVE_SLUGS = new Set(['nbne', 'my-live-client'])
const isDemo = !LIVE_SLUGS.has(TENANT_SLUG) && !LIVE_SLUGS.has(tenant.slug) && !!tenant.slug
```

### Staff page shows "No active staff"

**Cause:** Seed data has not run, or `staff_users` / `booking_staff` not configured for this tenant.

**Fix:**
1. Run the seed: `railway run python manage.py seed_demo --tenant SLUG`
2. If this is a new tenant, ensure `staff_users` and `booking_staff` are defined in the TENANTS dict

### Media uploads disappear after redeploy

**Cause:** R2 storage not configured. Railway filesystem is ephemeral.

**Fix:** Set the R2 env vars (see Section 4.5).

---

## 15. Live Instances Reference

### Current deployments (as of February 2026)

| Client | Tenant Slug | Railway Backend | Vercel Frontend | Custom Domain |
|--------|-------------|-----------------|-----------------|---------------|
| Salon X | `salon-x` | `salon-x-backend-production.up.railway.app` | `salon-x2.vercel.app` | - |
| Tavola | `restaurant-x` | `restaurant-x-backend-production.up.railway.app` | `tavola-gray.vercel.app` | - |
| FitHub | `health-club-x` | `health-club-x-backend-production.up.railway.app` | `fithub-lake.vercel.app` | - |
| NBNE | `nbne` | `nbneplatform-production.up.railway.app` | (multiple) | `app.nbnesigns.co.uk` |
| Mind Dept | `mind-department` | `nbneplatform-production.up.railway.app` | - | `app.theminddepartment.com` |

### Protected tenants

These are in the `LIVE_TENANTS` set in `seed_demo.py` and will NOT be seeded by default runs:

- `mind-department` (The Mind Department, live client)

---

## 16. Security Notes

### Credentials to rotate for production

1. **Django secret keys** must be unique per instance. Never share between projects.
2. **SMTP password** (`!49Monkswood`) is shared across all instances. Set up per-client email for production.
3. **R2 credentials** are shared. Consider per-client R2 API tokens for true isolation.
4. **Stripe keys** are currently test keys. Switch to live keys before accepting real payments.
5. **Demo passwords** (`admin123`) must be changed immediately for live clients.

### First login for live clients

1. Log in with the seeded owner credentials
2. Go to Settings and change the password
3. Invite real staff via the Staff module (sends email with set-password link)
4. Remove `SEED_TENANT` env var from Railway to prevent data reset on redeploy

### Data isolation

Each Railway project has its own Postgres database. There is no cross-tenant data access at the database level. The `SEED_TENANT` var ensures only one tenant's data exists per database.

The Cloudflare R2 bucket is shared, but files are stored with tenant-prefixed paths. For maximum isolation, create separate R2 API tokens per client.

---

## Quick Reference: Full Deployment Checklist

```
[ ] 1. Create Railway project:     railway init --name nbne-{slug}
[ ] 2. Add Postgres:               railway add -d postgres
[ ] 3. Add backend service:        railway add -s {slug}-backend -r NBNEORIGIN/nbne_platform
[ ] 4. Link to service:            railway link -p nbne-{slug} -s {slug}-backend
[ ] 5. Generate domain:            railway domain -s {slug}-backend
[ ] 6. Set RAILWAY_ROOT_DIRECTORY:  railway variable set "RAILWAY_ROOT_DIRECTORY=backend"
[ ] 7. Set Django env vars:         (secret key, debug, allowed hosts)
[ ] 8. Set module flags:            (all True for demo sites)
[ ] 9. Set SEED_TENANT:             railway variable set "SEED_TENANT={slug}"
[ ] 10. Set email env vars:         (IONOS SMTP)
[ ] 11. Set R2 storage env vars:    (Cloudflare R2)
[ ] 12. Set Stripe env vars:        (optional)
[ ] 13. Wait for Railway deploy to complete
[ ] 14. Create Vercel project from NBNEORIGIN/nbne_business, root: frontend
[ ] 15. Set Vercel env vars:        NEXT_PUBLIC_TENANT_SLUG, NEXT_PUBLIC_API_BASE_URL, DJANGO_BACKEND_URL
[ ] 16. Deploy Vercel
[ ] 17. Note the Vercel URL
[ ] 18. Set CORS on Railway:        CORS_ALLOWED_ORIGINS, CSRF_TRUSTED_ORIGINS
[ ] 19. Redeploy Railway
[ ] 20. Test: branding loads, login works, booking flow correct, admin panel functional
[ ] 21. (Optional) Add custom domain on Vercel + update CORS
[ ] 22. (Live clients) Remove SEED_TENANT, change passwords, add to LIVE_TENANTS
```

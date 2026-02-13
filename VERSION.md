# NBNE Business Platform — Revision 3

## Version
3.0.0

## Date
2026-02-13

## Summary
Rev 3 merges the battle-tested Mind Department backend (bookings, compliance, CRM, documents, email reminders, Smart Booking Engine, intake profiles, reports, timesheets) with the Rev 2 architecture (feature flags, accounts, auditlog, tenants, staff, analytics, payments). All client-specific branding has been removed and replaced with configurable settings.

## What's New (vs Rev 2)

### From The Mind Department (production-tested)
- **Full bookings module** — 20+ view files: availability engine, intake profiles, schedule management, working hours, timesheets, reports, demo data, SBE
- **Smart Booking Engine** — Risk scoring, demand indexing, backfill commands
- **Email reminders** — Background worker with 24h/1h booking reminders via SMTP
- **Owner invite system** — Token-based invite/password-reset with branded HTML emails
- **Intake profiles** — GDPR-compliant wellbeing disclaimers with renewal tracking
- **Class packages** — Multi-session passes with credit tracking
- **Reports module** — Revenue, utilisation, retention, staff hours, leave analytics
- **Timesheets** — Staff timesheet generation and management
- **Dashboard** — Owner dashboard with revenue, bookings, client health metrics
- **Stripe checkout** — Session-based checkout with webhook handling
- **Document vault seeding** — Default document placeholders
- **CRM sync** — Auto-sync leads from booking clients

### From Rev 2 (architecture)
- **Feature flags** — All 9 modules toggle via env vars
- **Accounts app** — Separate auth app with RBAC permissions
- **Audit log** — Request-level audit trail with middleware
- **Tenants app** — Multi-tenant settings model
- **Staff app** — Staff profiles, shifts, leave, training records
- **Analytics app** — Cross-module dashboard and recommendations
- **Payments app** — Stripe integration with feature flag

### Generalization
- `booking_platform/` renamed to `config/`
- All TMD-specific branding replaced with `EMAIL_BRAND_NAME` setting
- All hardcoded URLs replaced with `FRONTEND_URL` setting
- Conditional URL routing based on feature flags
- Generic seed data (no client-specific content)
- Configurable SMTP credentials (no hardcoded email addresses)

## Architecture

| Layer | Stack | Host |
|-------|-------|------|
| Backend | Django 5.2 + DRF + SimpleJWT | Railway |
| Database | PostgreSQL | Railway (managed) |
| Email | Configurable SMTP + Resend fallback | Any |
| Static | WhiteNoise | Railway |
| Admin UI | Jazzmin | Built-in |

## Apps

| App | Always | Flag | Purpose |
|-----|--------|------|---------|
| core | ✅ | — | Config, auth views, password tokens, tenant bridge |
| accounts | ✅ | — | RBAC permissions, user management |
| auditlog | ✅ | — | Request audit trail |
| bookings | — | BOOKINGS_MODULE_ENABLED | Full booking system |
| payments | — | PAYMENTS_MODULE_ENABLED | Stripe integration |
| staff | — | STAFF_MODULE_ENABLED | Staff profiles, shifts, leave |
| comms | — | COMMS_MODULE_ENABLED | Communications |
| compliance | — | COMPLIANCE_MODULE_ENABLED | UK HSE compliance |
| documents | — | DOCUMENTS_MODULE_ENABLED | Document vault |
| crm | — | CRM_MODULE_ENABLED | Lead management |
| analytics | — | ANALYTICS_MODULE_ENABLED | Dashboard & recommendations |
| tenants | — | TENANTS_MODULE_ENABLED | Multi-tenant settings |

## Demo Tenants (via seed_demo)
- **Salon X** — Hair salon with bookings, payments, staff, comms
- **Restaurant X** — Restaurant with bookings, staff, CRM
- **Health Club X** — Gym with bookings, payments, compliance, documents
- **Mind Department** — Mindfulness practice (production reference)
- **NBNE** — Internal dogfooding

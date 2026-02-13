# The Mind Department — Backend API

Django REST API powering The Mind Department booking and business management platform.

## Apps

| App | Purpose |
|-----|---------|
| `booking_platform` | Django project config, URL routing, settings |
| `core` | Config model, JWT auth views, password tokens, owner invite |
| `bookings` | Services, staff, clients, bookings, schedules, availability, intake, payments, SBE, reminders |
| `compliance` | UK HSE compliance items, categories, scoring, signals |
| `crm` | Lead management, booking sync |
| `comms` | Communications module |
| `documents` | Document vault with tagging |

## Management Commands

| Command | Description |
|---------|-------------|
| `setup_production` | Create default users, services, disclaimers, packages |
| `invite_owner` | Create owner account and send invite email |
| `seed_compliance` | Seed UK HSE baseline compliance items |
| `seed_document_vault` | Create default document placeholders |
| `sync_crm_leads` | Sync CRM leads from booking clients |
| `update_demand_index` | Update service demand scoring |
| `backfill_sbe_scores` | Backfill Smart Booking Engine risk scores |
| `send_booking_reminders` | Send 24h/1h booking reminder emails (supports `--loop`) |

## API Endpoints

### Auth (`/api/auth/`)
- `POST /login/` — JWT login
- `GET /me/` — Current user info
- `POST /me/set-password/` — Change password (authenticated)
- `POST /password-reset/` — Request reset email
- `GET /validate-token/` — Check token validity
- `POST /set-password-token/` — Set password via token
- `POST /invite/` — Resend owner invite

### Bookings (`/api/bookings/`)
- Services, staff, clients, bookings CRUD
- Availability and slot generation
- Dashboard summary
- Reports (revenue, utilisation, retention)
- Intake profiles and disclaimers
- Schedule management (business hours, closures, leave)
- Timesheets

### CRM (`/api/crm/`)
- Leads CRUD, sync from bookings

### Compliance (`/api/compliance/`)
- Items, categories, dashboard, calendar, CSV export

### Documents (`/api/documents/`)
- Document vault CRUD, tagging

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py setup_production
python manage.py runserver
```

## Deployment

Deployed on Railway. See root `README.md` for full deployment guide.

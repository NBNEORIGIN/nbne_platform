# Reset Notes - Per-Client Instance Architecture

**Date:** 2026-02-05
**Reason:** Transitioning from single Django app to per-client instance model

## Current State (Pre-Reset)

### What We Have
- Single Django project at `d:/nbne-booking-django`
- Working booking flow (Loop 8 complete)
- Models: Service, Staff, Client, Booking, Session
- APIs: Services, Staff, Bookings, Slots, Sessions
- UI: Complete Fresha-style booking flow (5 steps)
- Config system with branding support
- Seed data for testing

### Completed Work
- **Loops 0-7:** Foundation, APIs, booking models, slot generation
- **Loop 8:** House of Hair UI (Fresha-style) - COMPLETE
  - Service selection
  - Staff selection with "Any Professional"
  - Date/time picker with dynamic slots
  - Customer details with GDPR consent
  - Confirmation page

### Files to Preserve
- `bookings/models.py` - All booking models
- `bookings/api_views.py` - API endpoints
- `bookings/booking_views.py` - UI views
- `bookings/utils.py` - Slot generation logic
- `templates/bookings/` - All UI templates
- `core/models.py` - Config model
- `docs/` - All documentation

## New Architecture

### Target Structure
```
/base-backend/          # Django template (reusable)
/base-frontend/         # Shared Next.js frontend (optional)

/clients/
  /house-of-hair/
    backend/            # Django instance
    frontend/           # Next.js/React
    docker-compose.yml
    .env
    client.config.json
    backups/
    docs/

  /mind-department/
    backend/
    frontend/
    docker-compose.yml
    .env
    client.config.json
    backups/
    docs/
```

### Key Changes
1. **No Runtime Multi-Tenancy:** Each client = separate Django instance
2. **Physical Isolation:** Separate folders, databases, ports
3. **Config-Driven:** All customization via `client.config.json`
4. **Moveable:** Each instance can move between servers
5. **Independent Frontends:** Deploy to Vercel separately

## Migration Strategy

### Phase 1: Create Base Template
- Copy current Django project to `/base-backend`
- Clean up client-specific code
- Make everything config-driven
- Add environment variable support

### Phase 2: Client Instances
- Create `/clients/house-of-hair/backend` from base
- Create `/clients/mind-department/backend` from base
- Configure separate databases
- Configure separate ports

### Phase 3: Frontends
- Extract UI to Next.js/React
- Create `/clients/house-of-hair/frontend`
- Create `/clients/mind-department/frontend`
- Wire to respective backends

### Phase 4: Automation
- Create `scripts/new-client.sh` for instance creation
- Backup/restore scripts per instance
- Deployment documentation

## What Gets Preserved

### Models (Already Good)
- Service, Staff, Client, Booking, Session
- Config model for branding
- All relationships and constraints

### APIs (Already Good)
- `/api/services/`
- `/api/staff/`
- `/api/bookings/`
- `/api/bookings/slots/`
- `/api/sessions/`
- `/api/config/`

### UI Components (To Extract)
- Service selection
- Staff selection
- Date/time picker
- Booking form
- Confirmation page

## What Changes

### From Single App → Per-Client Instances
- **Before:** One Django app, one database
- **After:** Multiple Django instances, multiple databases

### From Hardcoded → Config-Driven
- **Before:** Branding in database Config model
- **After:** Branding in `client.config.json` + database

### From Monolith → Separated Frontend
- **Before:** Django templates
- **After:** Next.js/React + Django API

## Rollback Plan

If needed, current state is preserved:
- Git commit before changes
- Full backup of `d:/nbne-booking-django`
- Documentation of current structure

## Success Criteria

Loop 0 complete when:
- [x] This document created
- [x] Current state documented
- [x] Migration strategy defined
- [ ] Archive branch created (manual Git step)

## Notes

- Current Django project will become `/base-backend`
- UI templates will be reference for Next.js conversion
- All API endpoints remain compatible
- Database schema remains the same per instance

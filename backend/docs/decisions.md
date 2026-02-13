# Architecture Decisions

## Loop 8: House of Hair UI

### Decision: Django Session for State Management
**Date:** 2026-02-05
**Context:** Need to persist booking selections across multiple pages
**Decision:** Use Django session storage for booking state
**Alternatives Considered:**
- Query parameters (too long, security concerns)
- Local storage (requires more JS, sync issues)
- Hidden form fields (cumbersome, page-specific)

**Rationale:**
- Server-side state is more secure
- No JS required for state persistence
- Easy to clear on completion
- Works with browser back button
- Session expires automatically

**Implementation:**
```python
request.session['booking_service_id'] = service_id
request.session['booking_staff_id'] = staff_id
request.session['booking_date'] = date
request.session['booking_time'] = time
```

---

### Decision: Inline CSS in Templates
**Date:** 2026-02-05
**Context:** Need branded, responsive UI quickly
**Decision:** Embed CSS in Django templates with template variables
**Alternatives Considered:**
- External CSS files (harder to brand dynamically)
- CSS-in-JS (adds complexity)
- Tailwind CSS (requires build step)

**Rationale:**
- Dynamic branding via `{{ branding.primaryColor }}`
- No build step required
- Single-file components easier to understand
- Fast iteration for demo
- Can extract to static files later if needed

**Trade-offs:**
- CSS linter errors (expected, safe to ignore)
- Larger HTML payload
- No CSS caching between pages

---

### Decision: Auto-Submit on Selection (Steps 1-2)
**Date:** 2026-02-05
**Context:** Service and staff selection steps
**Decision:** Auto-submit form when radio button selected
**Alternatives Considered:**
- Explicit "Continue" button
- Next/Previous navigation
- Multi-step form on one page

**Rationale:**
- Matches Fresha UX (inspiration)
- Reduces clicks (faster flow)
- Clear intent when selecting
- Mobile-friendly (no extra tap)

**Implementation:**
```javascript
radio.addEventListener('change', function() {
    document.getElementById('form').submit();
});
```

---

### Decision: AJAX Slot Loading
**Date:** 2026-02-05
**Context:** Date/time selection needs dynamic slot availability
**Decision:** Load slots via fetch() when date changes
**Alternatives Considered:**
- Pre-load all dates (too much data)
- Full page reload (slower UX)
- WebSocket (overkill)

**Rationale:**
- Fast, responsive UX
- Only load needed data
- Easy to show loading states
- Handles errors gracefully
- Vanilla JS (no dependencies)

**Implementation:**
```javascript
fetch(`/book/time/slots/?service_id=${id}&staff_id=${id}&date=${date}`)
    .then(response => response.json())
    .then(data => renderSlots(data.slots));
```

---

### Decision: Summary Panel Layout
**Date:** 2026-02-05
**Context:** Need to show booking context during selection
**Decision:** Right-side panel (desktop), sticky bottom (mobile)
**Alternatives Considered:**
- Top summary bar
- Collapsible sidebar
- Modal on demand
- No summary (rely on memory)

**Rationale:**
- Desktop: Persistent context without scrolling
- Mobile: Sticky bottom doesn't block content
- Updates in real-time as selections change
- Shows price prominently
- Fresha-style pattern

---

### Decision: Two-Tier Consent Model
**Date:** 2026-02-05
**Context:** GDPR compliance and marketing opt-in
**Decision:** Separate required (booking) and optional (marketing) consent
**Alternatives Considered:**
- Single consent checkbox
- Opt-out model
- No consent (non-compliant)

**Rationale:**
- GDPR requires explicit consent
- Booking comms necessary for service
- Marketing separate and optional
- Clear, transparent to user
- Legally compliant

**Implementation:**
- Booking consent: Required checkbox, blocks submission
- Marketing consent: Optional checkbox, stored in notes
- Both stored with booking for audit trail

---

### Decision: Session Clearing on Confirmation
**Date:** 2026-02-05
**Context:** Prevent double-booking on refresh
**Decision:** Clear booking session data after confirmation page renders
**Alternatives Considered:**
- Keep session (allow editing)
- Redirect to prevent refresh
- Token-based one-time confirmation

**Rationale:**
- Prevents accidental double-booking
- Clean state for next booking
- Simple implementation
- Refresh shows same confirmation (safe)

---

### Decision: "Any Professional" Implementation
**Date:** 2026-02-05
**Context:** Allow booking without staff preference
**Decision:** Store staff_id='any', resolve to first available on booking creation
**Alternatives Considered:**
- Random staff assignment
- Round-robin distribution
- Least-busy staff
- Null staff_id

**Rationale:**
- Simple to implement
- Predictable behavior
- Can enhance later with smart assignment
- Matches user expectation ("first available")

**Implementation:**
```python
if staff_id == 'any':
    staff = Staff.objects.filter(active=True, services=service).first()
```

---

### Decision: Booking Reference Format
**Date:** 2026-02-05
**Context:** Need user-friendly booking identifier
**Decision:** Use booking ID with zero-padding (#00001, #00002, etc.)
**Alternatives Considered:**
- UUID (too long, not memorable)
- Random code (requires uniqueness check)
- Date-based (YYYYMMDD-001)

**Rationale:**
- Simple, sequential
- Easy to communicate verbally
- Short enough to remember
- No collision risk
- Can enhance later with prefix (e.g., HH-00001)

**Implementation:**
```python
booking_reference = f"#{booking.id:05d}"
```

---

## Future Decisions Needed

### Email Templates (Loop 10)
- Plain text vs HTML
- Template engine choice
- Transactional email service

### SMS Integration (Loop 11)
- SMS provider selection
- Message templates
- Opt-in/opt-out handling

### Client Portal (Loop 12)
- Authentication method
- Booking management features
- Profile editing

### GDPR Compliance (Loop 13)
- Data retention policies
- Export/deletion requests
- Privacy policy integration

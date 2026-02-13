# UX Notes - House of Hair Booking Flow

## Design Philosophy
Fresha-inspired booking experience with:
- Clean, minimal interface
- Mobile-first responsive design
- Clear progress indication
- Fast, intuitive flow

## Color System
All colors pulled from `Config` model (branding category):
- Primary: `branding.primaryColor` (default: #3B82F6 blue)
- Secondary: `branding.secondaryColor` (default: #10B981 green)
- Client name: `branding.clientName`

## Booking Flow

### Step 1: Service Selection (`/book`)
**Layout:** Grid of service cards
**Features:**
- Service name, description, duration, price
- Click-to-select (auto-submit)
- Mobile: Single column
- Desktop: Multi-column grid

**UX Decisions:**
- No "Continue" button needed - selection auto-advances
- Price prominently displayed
- Duration shown for time planning

### Step 2: Staff Selection (`/book/staff`)
**Layout:** Grid of staff cards with "Any Professional" option
**Features:**
- "Any Professional" card with gradient background (featured)
- Staff cards with avatar (first initial)
- Service info summary at top
- Click-to-select (auto-submit)

**UX Decisions:**
- "Any" option placed first and visually distinct
- Staff photos replaced with initials (placeholder for real photos)
- Service context maintained throughout

### Step 3: Date & Time Selection (`/book/time`)
**Layout:** Two-column (desktop) with summary panel
**Features:**
- Horizontal scrolling date pills (14 days)
- Time slots grid (15-min intervals)
- Dynamic loading via AJAX
- Summary panel (sticky on mobile)
- "No availability" state
- Loading skeleton

**UX Decisions:**
- Date pills for quick scanning
- Time slots update without page reload
- Summary panel keeps context visible
- Selected time highlighted in summary
- Continue button disabled until time selected

**States Handled:**
- Loading: "Loading available times..."
- No slots: "No available times for this date..."
- Slot selected: Summary updates, button enabled
- Error: "Error loading times. Please try again."

### Step 4: Customer Details (`/book/details`)
**Layout:** Single column form with summary box
**Features:**
- Booking summary at top (read-only)
- Name, email, phone (required)
- Special requests (optional textarea)
- Two consent checkboxes
- Form validation

**UX Decisions:**
- Summary box reinforces commitment
- Consent separated: booking (required) vs marketing (optional)
- Clear GDPR compliance
- Validation prevents incomplete submissions

**Consent Types:**
1. **Booking Communications (Required)**
   - Email/SMS confirmations and reminders
   - Cannot book without this
2. **Marketing Communications (Optional)**
   - Promotional offers and news
   - Separate opt-in

### Step 5: Confirmation (`/book/confirm`)
**Layout:** Centered confirmation card
**Features:**
- Success icon (green checkmark)
- Booking reference number
- Full booking details
- Email confirmation notice
- Action buttons (home, book another)

**UX Decisions:**
- Clear success state
- Reference number for support
- Email notice sets expectation
- Session cleared to prevent double-booking
- Easy path to book again

## Progress Indicator
4-step progress bar in header:
1. Service (blue when active, green when complete)
2. Staff
3. Date/Time
4. Details

## Responsive Breakpoints
- Mobile: < 768px
  - Single column layouts
  - Sticky summary panel at bottom
  - Full-width buttons
- Desktop: ≥ 768px
  - Multi-column grids
  - Right-side summary panel
  - Wider forms

## Accessibility
- Keyboard navigation supported
- Focus states on all interactive elements
- Semantic HTML structure
- Color contrast meets WCAG AA
- Form labels properly associated
- Required fields marked with asterisk

## Performance
- AJAX slot loading (no full page reload)
- Minimal JavaScript (vanilla JS, no frameworks)
- CSS in templates (no external files for demo)
- Session-based state (no complex client state)

## Error States
- Form validation errors shown inline
- API errors shown with retry option
- "Slot taken" message if booking fails
- Network errors handled gracefully

## Future Enhancements (Not in Loop 8)
- Add-to-calendar links
- SMS confirmation (Loop 11)
- Email templates (Loop 10)
- Staff photos/bios
- Service images
- Reviews/ratings
- Waitlist functionality
- Rescheduling flow
- Cancellation flow

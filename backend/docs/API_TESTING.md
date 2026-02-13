# API Testing Guide

## Base URL
`http://localhost:8000/api/`

## Config Endpoints

### Get All Config
```bash
GET /api/config/
```
Returns all configuration entries.

### Get Branding Config
```bash
GET /api/config/branding/
```
Returns: `{"clientName": "...", "primaryColor": "...", ...}`

### Get Feature Flags
```bash
GET /api/config/features/
```
Returns: `{"enableSMS": "false", "enablePortal": "true", ...}`

### Get Config by Category
```bash
GET /api/config/by_category/
```
Returns all config grouped by category.

## Service Endpoints

### List Services
```bash
GET /api/services/
```
Returns all active services.

### Get Service
```bash
GET /api/services/{id}/
```

### Create Service
```bash
POST /api/services/
Content-Type: application/json

{
  "name": "Haircut",
  "description": "Professional haircut",
  "duration_minutes": 30,
  "price": "35.00",
  "active": true
}
```

## Staff Endpoints

### List Staff
```bash
GET /api/staff/
```
Returns all active staff with their services.

### Get Staff Member
```bash
GET /api/staff/{id}/
```

## Booking Endpoints

### List Bookings
```bash
GET /api/bookings/
```

### Get Available Time Slots
```bash
GET /api/bookings/slots/?staff_id=1&service_id=1&date=2026-02-06
```
Returns available time slots for the specified staff, service, and date.

**Parameters:**
- `staff_id` (required): Staff member ID
- `service_id` (required): Service ID
- `date` (required): Date in YYYY-MM-DD format

**Response:**
```json
{
  "slots": [
    {
      "start_time": "2026-02-06T09:00:00+00:00",
      "end_time": "2026-02-06T09:30:00+00:00",
      "available": true
    },
    ...
  ]
}
```

### Get Available Dates
```bash
GET /api/bookings/available_dates/?staff_id=1&service_id=1&days_ahead=30
```
Returns dates with available slots.

**Parameters:**
- `staff_id` (required): Staff member ID
- `service_id` (required): Service ID
- `days_ahead` (optional): Number of days to look ahead (default: 30)

**Response:**
```json
{
  "available_dates": [
    {
      "date": "2026-02-05",
      "available_slots": 32
    },
    ...
  ]
}
```

### Create Booking
```bash
POST /api/bookings/
Content-Type: application/json

{
  "client": 1,
  "service": 1,
  "staff": 1,
  "start_time": "2026-02-06T10:00:00Z",
  "status": "pending",
  "notes": "First appointment"
}
```

## Session Endpoints

### List Sessions
```bash
GET /api/sessions/
```

### Get Upcoming Sessions
```bash
GET /api/sessions/upcoming/
```
Returns only future sessions, ordered by start time.

### Enroll in Session
```bash
POST /api/sessions/{id}/enroll/
Content-Type: application/json

{
  "client_id": 1
}
```

**Response:**
- 200: Successfully enrolled
- 400: Session is full or missing client_id
- 404: Client not found

## Client Endpoints

### List Clients
```bash
GET /api/clients/
```

### Create Client
```bash
POST /api/clients/
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "555-1234",
  "notes": "Prefers morning appointments"
}
```

## Health Check

### System Health
```bash
GET /health/
```
Returns system status and database connectivity.

## Testing with PowerShell

### Get Services
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/services/" -UseBasicParsing | ConvertFrom-Json
```

### Get Available Slots
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/bookings/slots/?staff_id=1&service_id=1&date=2026-02-06" -UseBasicParsing | ConvertFrom-Json
```

### Create Booking
```powershell
$body = @{
    client = 1
    service = 1
    staff = 1
    start_time = "2026-02-06T15:00:00Z"
    status = "pending"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/bookings/" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
```

## Testing with curl

### Get Services
```bash
curl http://localhost:8000/api/services/
```

### Get Available Slots
```bash
curl "http://localhost:8000/api/bookings/slots/?staff_id=1&service_id=1&date=2026-02-06"
```

### Create Booking
```bash
curl -X POST http://localhost:8000/api/bookings/ \
  -H "Content-Type: application/json" \
  -d '{
    "client": 1,
    "service": 1,
    "staff": 1,
    "start_time": "2026-02-06T15:00:00Z",
    "status": "pending"
  }'
```

## Sample Data

After running `python manage.py seed_bookings`, you'll have:

**Services:**
1. Haircut (30min, $35)
2. Hair Color (90min, $85)
3. Therapy Session (60min, $120)
4. Group Therapy (90min, $45)

**Staff:**
1. Sarah Johnson (Haircut, Hair Color)
2. Mike Chen (Haircut)
3. Dr. Emily Smith (Therapy Session, Group Therapy)

**Clients:**
1. John Doe
2. Jane Smith

**Bookings:**
- John Doe → Haircut with Sarah @ 2026-02-06 10:00
- Jane Smith → Hair Color with Sarah @ 2026-02-06 14:00

**Sessions:**
- Mindfulness & Meditation (Group Therapy) @ 2026-02-12 18:00 (2/10 enrolled)

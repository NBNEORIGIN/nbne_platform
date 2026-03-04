#!/bin/bash
set -e

echo "=== Checking salon-x .env for Stripe vars ==="
grep -i stripe /opt/nbne/instances/salon-x/.env 2>/dev/null || echo "No STRIPE vars in .env"

echo ""
echo "=== Checking Django settings for Stripe ==="
docker exec salon-x-backend-1 python manage.py shell -c "
from django.conf import settings
print('STRIPE_SECRET_KEY set:', bool(getattr(settings, 'STRIPE_SECRET_KEY', '')))
sk = getattr(settings, 'STRIPE_SECRET_KEY', '')
print('STRIPE_SECRET_KEY prefix:', sk[:10] + '...' if sk else 'EMPTY')
print('STRIPE_WEBHOOK_SECRET set:', bool(getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')))
print('PAYMENTS_ENABLED:', getattr(settings, 'PAYMENTS_ENABLED', 'NOT SET'))
"

echo ""
echo "=== Testing checkout endpoint (direct to Django) ==="
curl -s -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Slug: salon-x' \
  -d '{"service_id":1,"staff_id":1,"date":"2026-03-10","time":"11:00","client_name":"Test User","client_email":"test@example.com","client_phone":"07700000000"}' \
  http://127.0.0.1:8001/api/checkout/create/
echo ""

echo ""
echo "=== Testing checkout via Next.js proxy ==="
curl -s -X POST \
  -H 'Content-Type: application/json' \
  -d '{"service_id":1,"staff_id":1,"booking_date":"2026-03-10","booking_time":"11:00","customer_name":"Test User","customer_email":"test@example.com","customer_phone":"07700000000"}' \
  http://127.0.0.1:3001/api/checkout/create/
echo ""

echo "=== DONE ==="

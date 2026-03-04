#!/bin/bash
set -e

echo "=== Checking Stripe config for salon-x ==="
docker exec salon-x-backend-1 python -c "
from django.conf import settings
print('STRIPE_SECRET_KEY set:', bool(getattr(settings, 'STRIPE_SECRET_KEY', '')))
print('STRIPE_SECRET_KEY prefix:', getattr(settings, 'STRIPE_SECRET_KEY', '')[:7] if getattr(settings, 'STRIPE_SECRET_KEY', '') else 'EMPTY')
print('STRIPE_WEBHOOK_SECRET set:', bool(getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')))
print('PAYMENTS_ENABLED:', getattr(settings, 'PAYMENTS_ENABLED', 'NOT SET'))
print('DEFAULT_CURRENCY:', getattr(settings, 'DEFAULT_CURRENCY', 'NOT SET'))
"

echo ""
echo "=== Checking salon-x .env for Stripe vars ==="
grep -i stripe /opt/nbne/instances/salon-x/.env 2>/dev/null || echo "No STRIPE vars in .env"

echo ""
echo "=== Testing checkout endpoint ==="
curl -s -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Slug: salon-x' \
  -d '{"service_id":1,"staff_id":1,"date":"2026-03-10","time":"11:00","client_name":"Test User","client_email":"test@example.com","client_phone":"07700000000"}' \
  http://127.0.0.1:8001/api/checkout/create/ | python3 -m json.tool 2>/dev/null || echo "RAW response above"

echo ""
echo "=== DONE ==="

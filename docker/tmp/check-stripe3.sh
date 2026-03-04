#!/bin/bash
set -e

echo "=== 1. Stripe env vars in salon-x .env ==="
grep -i stripe /opt/nbne/instances/salon-x/.env 2>/dev/null || echo "No STRIPE vars found"

echo ""
echo "=== 2. Django Stripe settings ==="
docker exec salon-x-backend-1 python manage.py shell -c "
from django.conf import settings
sk = getattr(settings, 'STRIPE_SECRET_KEY', '')
wh = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
pe = getattr(settings, 'PAYMENTS_ENABLED', 'NOT_SET')
print('STRIPE_KEY_PREFIX:', sk[:12] if sk else 'EMPTY')
print('WEBHOOK_SECRET:', 'SET' if wh else 'EMPTY')
print('PAYMENTS_ENABLED:', pe)
"

echo ""
echo "=== 3. Test checkout create (direct to Django 8001) ==="
RESULT=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Slug: salon-x' \
  -H 'Host: salon-x.nbne.uk' \
  -d '{"service_id":1,"staff_id":1,"date":"2026-03-10","time":"11:00","client_name":"Test","client_email":"test@test.com","client_phone":"07700000000"}' \
  http://127.0.0.1:8001/api/checkout/create/)
echo "HTTP Status: $RESULT"

BODY=$(curl -s -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Slug: salon-x' \
  -H 'Host: salon-x.nbne.uk' \
  -d '{"service_id":1,"staff_id":1,"date":"2026-03-10","time":"11:00","client_name":"Test","client_email":"test@test.com","client_phone":"07700000000"}' \
  http://127.0.0.1:8001/api/checkout/create/)
echo "Response: $BODY"

echo ""
echo "=== 4. Check ALLOWED_HOSTS ==="
docker exec salon-x-backend-1 python manage.py shell -c "
from django.conf import settings
print('ALLOWED_HOSTS:', settings.ALLOWED_HOSTS)
"

echo ""
echo "=== DONE ==="

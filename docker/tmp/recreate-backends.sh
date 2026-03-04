#!/bin/bash
set -e

for INST in salon-x restaurant-x health-club-x nbne; do
  cd /opt/nbne/instances/$INST
  docker compose -p $INST --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml up -d --no-deps --force-recreate backend
  echo "$INST backend recreated"
done

echo ""
echo "Waiting 8s for backends to start..."
sleep 8

echo "=== Verify salon-x Stripe config ==="
docker exec salon-x-backend-1 python manage.py shell -c "
from django.conf import settings
sk = getattr(settings, 'STRIPE_SECRET_KEY', '')
print('STRIPE_KEY_PREFIX:', sk[:12] if sk else 'EMPTY')
print('WEBHOOK_SECRET:', 'SET' if getattr(settings, 'STRIPE_WEBHOOK_SECRET', '') else 'EMPTY')
"

echo ""
echo "=== Test checkout endpoint ==="
curl -s -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Slug: salon-x' \
  -H 'Host: salon-x.nbne.uk' \
  -d '{"service_id":1,"staff_id":1,"date":"2026-03-10","time":"11:00","client_name":"Test","client_email":"test@test.com","client_phone":"07700000000"}' \
  http://127.0.0.1:8001/api/checkout/create/ | head -c 500
echo ""

echo "=== ALL DONE ==="

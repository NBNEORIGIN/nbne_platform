#!/bin/bash
set -e

echo "=== List salon-x services ==="
docker exec salon-x-backend-1 python manage.py shell -c "
from bookings.models import Service
for s in Service.objects.all()[:5]:
    print(f'Service id={s.id} name={s.name} price={s.price} deposit_pence={getattr(s, \"deposit_pence\", None)} duration={s.duration_minutes}min')
"

echo ""
echo "=== List salon-x staff ==="
docker exec salon-x-backend-1 python manage.py shell -c "
from bookings.models import Staff
for s in Staff.objects.all()[:5]:
    print(f'Staff id={s.id} name={s.name}')
"

echo ""
echo "=== Test checkout with valid IDs ==="
# Will use the first service and staff IDs from above
SVC_ID=$(docker exec salon-x-backend-1 python manage.py shell -c "from bookings.models import Service; print(Service.objects.first().id)")
STAFF_ID=$(docker exec salon-x-backend-1 python manage.py shell -c "from bookings.models import Staff; print(Staff.objects.first().id)")
echo "Using service_id=$SVC_ID staff_id=$STAFF_ID"

curl -s -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Slug: salon-x' \
  -H 'Host: salon-x.nbne.uk' \
  -H 'Origin: https://salon-x.nbne.uk' \
  -d "{\"service_id\":$SVC_ID,\"staff_id\":$STAFF_ID,\"date\":\"2026-03-10\",\"time\":\"11:00\",\"client_name\":\"Test User\",\"client_email\":\"test@example.com\",\"client_phone\":\"07700000000\"}" \
  http://127.0.0.1:8001/api/checkout/create/
echo ""

echo "=== DONE ==="

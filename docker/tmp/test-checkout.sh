#!/bin/bash
set -e

echo "=== Test checkout create (direct to Django 8001) ==="
curl -sv -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Slug: salon-x' \
  -H 'Host: salon-x.nbne.uk' \
  -d '{"service_id":1,"staff_id":1,"date":"2026-03-10","time":"11:00","client_name":"Test User","client_email":"test@example.com","client_phone":"07700000000"}' \
  http://127.0.0.1:8001/api/checkout/create/ 2>&1 | tail -20
echo ""

echo "=== Check backend logs for errors ==="
docker logs salon-x-backend-1 --tail 30 2>&1 | grep -i -E "error|stripe|checkout|500|503|traceback" | tail -15
echo ""

echo "=== DONE ==="

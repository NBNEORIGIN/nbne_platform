#!/bin/bash
set -e

echo "=== Test checkout with valid IDs (service=51 Balayage, staff=20 Chloe) ==="
curl -s -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Slug: salon-x' \
  -H 'Host: salon-x.nbne.uk' \
  -H 'Origin: https://salon-x.nbne.uk' \
  -d '{"service_id":51,"staff_id":20,"date":"2026-03-10","time":"11:00","client_name":"Test User","client_email":"test@example.com","client_phone":"07700000000"}' \
  http://127.0.0.1:8001/api/checkout/create/
echo ""

echo "=== DONE ==="

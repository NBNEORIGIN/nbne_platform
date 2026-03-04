#!/bin/bash
set -e

echo "=== 1. Get a JWT token (direct Django login) ==="
RESP=$(curl -s -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Slug: salon-x' \
  -d '{"username":"salon-x-owner","password":"admin123"}' \
  http://127.0.0.1:8001/api/auth/login/)
echo "Login response: $RESP"

TOKEN=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access',''))" 2>/dev/null || echo "")
if [ -z "$TOKEN" ]; then
  echo "Failed to get token, trying with email..."
  RESP=$(curl -s -X POST \
    -H 'Content-Type: application/json' \
    -H 'X-Tenant-Slug: salon-x' \
    -d '{"username":"owner@salon-x.demo","password":"admin123"}' \
    http://127.0.0.1:8001/api/auth/login/)
  echo "Login response: $RESP"
  TOKEN=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access',''))" 2>/dev/null || echo "")
fi

if [ -z "$TOKEN" ]; then
  echo "FAILED to get token. Checking available users..."
  docker exec salon-x-backend-1 python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
for u in User.objects.filter(is_active=True)[:5]:
    print(f'{u.username} / {u.email} / staff={u.is_staff} super={u.is_superuser}')
"
  exit 1
fi

echo "Token: ${TOKEN:0:20}..."

echo ""
echo "=== 2. Test document list (direct to Django) ==="
curl -s -w "\nHTTP %{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'X-Tenant-Slug: salon-x' \
  http://127.0.0.1:8001/api/documents/ | tail -3
echo ""

echo ""
echo "=== 3. Test document upload (direct to Django) ==="
echo "test file content" > /tmp/test-doc.txt
curl -s -w "\nHTTP %{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'X-Tenant-Slug: salon-x' \
  -F "title=Test Upload" \
  -F "category=General" \
  -F "file=@/tmp/test-doc.txt" \
  http://127.0.0.1:8001/api/documents/create/
echo ""

echo ""
echo "=== 4. Test via Nginx ==="
curl -s -w "\nHTTP %{http_code}" -k \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Host: salon-x.nbne.uk' \
  -F "title=Test Nginx Upload" \
  -F "category=General" \
  -F "file=@/tmp/test-doc.txt" \
  https://127.0.0.1/api/documents/create/
echo ""

rm -f /tmp/test-doc.txt
echo ""
echo "=== DONE ==="

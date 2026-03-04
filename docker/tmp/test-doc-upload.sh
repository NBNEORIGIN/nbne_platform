#!/bin/bash
set -e

echo "=== 1. Get a JWT token ==="
TOKEN=$(curl -s -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Slug: salon-x' \
  -d '{"username":"owner@salon-x.demo","password":"admin123"}' \
  http://127.0.0.1:8001/api/auth/login/ | python3 -c "import sys,json; print(json.load(sys.stdin).get('access',''))")
echo "Token prefix: ${TOKEN:0:20}..."

echo ""
echo "=== 2. Test document list (direct to Django) ==="
curl -s -o /dev/null -w "HTTP %{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'X-Tenant-Slug: salon-x' \
  http://127.0.0.1:8001/api/documents/
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
echo "=== 4. Test document upload via Nginx ==="
curl -s -w "\nHTTP %{http_code}" -k \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Host: salon-x.nbne.uk' \
  -F "title=Test Upload Nginx" \
  -F "category=General" \
  -F "file=@/tmp/test-doc.txt" \
  https://127.0.0.1/api/documents/create/
echo ""

echo ""
echo "=== 5. Test WITHOUT token (should fail) ==="
curl -s -w "\nHTTP %{http_code}" \
  -H 'X-Tenant-Slug: salon-x' \
  -F "title=No Auth Test" \
  -F "file=@/tmp/test-doc.txt" \
  http://127.0.0.1:8001/api/documents/create/
echo ""

rm -f /tmp/test-doc.txt
echo ""
echo "=== DONE ==="

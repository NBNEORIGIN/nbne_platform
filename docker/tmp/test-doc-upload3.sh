#!/bin/bash
set -e

echo "=== 1. Get JWT token via Next.js proxy ==="
RESP=$(curl -s -X POST \
  -H 'Content-Type: application/json' \
  -H 'Host: salon-x.nbne.uk' \
  -k \
  -d '{"username":"owner","password":"admin123"}' \
  https://127.0.0.1/api/auth)
echo "Login: $(echo "$RESP" | head -c 200)"

TOKEN=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access',''))" 2>/dev/null || echo "")
if [ -z "$TOKEN" ]; then
  echo "Token empty, trying email login..."
  RESP=$(curl -s -X POST \
    -H 'Content-Type: application/json' \
    -H 'Host: salon-x.nbne.uk' \
    -k \
    -d '{"username":"owner@salon-x.demo","password":"admin123"}' \
    https://127.0.0.1/api/auth)
  echo "Login: $(echo "$RESP" | head -c 200)"
  TOKEN=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access',''))" 2>/dev/null || echo "")
fi

if [ -z "$TOKEN" ]; then
  echo "STILL no token. Exiting."
  exit 1
fi
echo "Token: ${TOKEN:0:30}..."

echo ""
echo "=== 2. Test /api/documents/create/ (with trailing slash, via Nginx) ==="
echo "test file" > /tmp/test-doc.txt
curl -sv -w "\nHTTP_CODE: %{http_code}" -k \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Host: salon-x.nbne.uk' \
  -F "title=Test Upload" \
  -F "category=General" \
  -F "file=@/tmp/test-doc.txt" \
  https://127.0.0.1/api/documents/create/ 2>&1 | grep -E "< HTTP|< Location|HTTP_CODE|detail|error|Authentication"
echo ""

echo ""
echo "=== 3. Test /api/documents/create (WITHOUT trailing slash, via Nginx) ==="
curl -sv -w "\nHTTP_CODE: %{http_code}" -k \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Host: salon-x.nbne.uk' \
  -F "title=Test Upload 2" \
  -F "category=General" \
  -F "file=@/tmp/test-doc.txt" \
  https://127.0.0.1/api/documents/create 2>&1 | grep -E "< HTTP|< Location|HTTP_CODE|detail|error|Authentication"
echo ""

rm -f /tmp/test-doc.txt
echo "=== DONE ==="

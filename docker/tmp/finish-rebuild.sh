#!/bin/bash
set -e

echo "=== Check salon-x backend ==="
curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1:8001/api/ || echo "UNREACHABLE"
echo ""
docker exec salon-x-backend-1 grep APPEND_SLASH /app/config/settings.py

echo ""
echo "=== Rebuild remaining 3 backends ==="
for INST in restaurant-x health-club-x nbne; do
  cd /opt/nbne/instances/$INST
  docker compose -p $INST --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml build --no-cache backend 2>&1 | tail -5
  docker compose -p $INST --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml up -d --no-deps backend
  echo "$INST rebuilt"
done

echo ""
echo "Waiting 20s for all backends..."
sleep 20

echo "=== Test upload end-to-end ==="
RESP=$(curl -s -X POST \
  -H 'Content-Type: application/json' \
  -H 'Host: salon-x.nbne.uk' \
  -k \
  -d '{"username":"owner","password":"admin123"}' \
  https://127.0.0.1/api/auth)
TOKEN=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access',''))" 2>/dev/null)
echo "Token: ${TOKEN:0:20}..."

echo "test content" > /tmp/test-doc.txt

echo "With trailing slash:"
curl -s -w "\nHTTP %{http_code}" -k \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Host: salon-x.nbne.uk' \
  -F "title=Test Slash" \
  -F "category=General" \
  -F "file=@/tmp/test-doc.txt" \
  https://127.0.0.1/api/documents/create/ | tail -3
echo ""

echo "Without trailing slash:"
curl -s -w "\nHTTP %{http_code}" -k \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Host: salon-x.nbne.uk' \
  -F "title=Test No Slash" \
  -F "category=General" \
  -F "file=@/tmp/test-doc.txt" \
  https://127.0.0.1/api/documents/create | tail -3
echo ""

rm -f /tmp/test-doc.txt
echo "=== ALL DONE ==="

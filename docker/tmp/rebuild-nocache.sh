#!/bin/bash
set -e

echo "=== Check git status ==="
cd /opt/nbne/shared
git log --oneline -3
echo ""
grep -n APPEND_SLASH backend/config/settings.py || echo "APPEND_SLASH not found in source!"

echo ""
echo "=== Rebuild salon-x backend (no cache) ==="
cd /opt/nbne/instances/salon-x
docker compose -p salon-x --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml build --no-cache backend
docker compose -p salon-x --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml up -d --no-deps backend
echo "salon-x rebuilt"

echo ""
echo "Waiting 15s..."
sleep 15

echo "=== Verify ==="
docker exec salon-x-backend-1 grep APPEND_SLASH /app/config/settings.py
curl -s -o /dev/null -w "Direct backend: HTTP %{http_code}" http://127.0.0.1:8001/api/
echo ""

echo ""
echo "=== Rebuild remaining 3 ==="
for INST in restaurant-x health-club-x nbne; do
  cd /opt/nbne/instances/$INST
  docker compose -p $INST --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml build --no-cache backend
  docker compose -p $INST --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml up -d --no-deps backend
  echo "$INST rebuilt"
done

echo ""
echo "Waiting 15s..."
sleep 15

echo "=== Test upload ==="
RESP=$(curl -s -X POST \
  -H 'Content-Type: application/json' \
  -H 'Host: salon-x.nbne.uk' \
  -k \
  -d '{"username":"owner","password":"admin123"}' \
  https://127.0.0.1/api/auth)
TOKEN=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access',''))")
echo "Token: ${TOKEN:0:20}..."

echo "test content" > /tmp/test-doc.txt
curl -s -w "\nHTTP %{http_code}" -k \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Host: salon-x.nbne.uk' \
  -F "title=Test Upload Final" \
  -F "category=General" \
  -F "file=@/tmp/test-doc.txt" \
  https://127.0.0.1/api/documents/create/ | tail -5
echo ""
rm -f /tmp/test-doc.txt

echo "=== ALL DONE ==="

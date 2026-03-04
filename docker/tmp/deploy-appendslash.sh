#!/bin/bash
set -e

cd /opt/nbne/shared && git pull origin main

for INST in salon-x restaurant-x health-club-x nbne; do
  cd /opt/nbne/instances/$INST
  docker compose -p $INST --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml up -d --no-deps --force-recreate backend
  echo "$INST backend recreated"
done

echo ""
echo "Waiting 8s..."
sleep 8

echo "=== Verify APPEND_SLASH ==="
docker exec salon-x-backend-1 python manage.py shell -c "
from django.conf import settings
print('APPEND_SLASH:', settings.APPEND_SLASH)
"

echo ""
echo "=== Test upload via Nginx ==="
RESP=$(curl -s -X POST \
  -H 'Content-Type: application/json' \
  -H 'Host: salon-x.nbne.uk' \
  -k \
  -d '{"username":"owner","password":"admin123"}' \
  https://127.0.0.1/api/auth)
TOKEN=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access',''))")

echo "test file" > /tmp/test-doc.txt
echo "With trailing slash:"
curl -s -w " HTTP %{http_code}" -k \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Host: salon-x.nbne.uk' \
  -F "title=Test With Slash" \
  -F "category=General" \
  -F "file=@/tmp/test-doc.txt" \
  https://127.0.0.1/api/documents/create/ | tail -c 100
echo ""

echo "Without trailing slash:"
curl -s -w " HTTP %{http_code}" -k \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Host: salon-x.nbne.uk' \
  -F "title=Test No Slash" \
  -F "category=General" \
  -F "file=@/tmp/test-doc.txt" \
  https://127.0.0.1/api/documents/create | tail -c 100
echo ""

rm -f /tmp/test-doc.txt
echo "=== DONE ==="

#!/bin/bash
set -e

echo "=== Pull latest ==="
cd /opt/nbne/shared
git pull origin main

echo ""
echo "=== Rebuild salon-x frontend ==="
cd /opt/nbne/instances/salon-x
docker compose -p salon-x --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml build --no-cache frontend 2>&1 | tail -10
docker compose -p salon-x --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml up -d --no-deps frontend
echo "salon-x frontend rebuilt"

echo ""
echo "Waiting 10s..."
sleep 10

echo "=== Verify ==="
curl -s -k -o /dev/null -w "salon-x frontend: HTTP %{http_code}" -H 'Host: salon-x.nbne.uk' https://127.0.0.1/book
echo ""
echo "=== DONE ==="

#!/bin/bash
set -e

echo "=== Rebuilding all 4 frontends with middleware fix ==="

for INSTANCE in salon-x restaurant-x health-club-x nbne; do
  echo "--- Stopping $INSTANCE frontend ---"
  cd /opt/nbne/instances/$INSTANCE
  docker compose -p $INSTANCE --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml stop frontend 2>/dev/null || true
  docker compose -p $INSTANCE --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml rm -f frontend 2>/dev/null || true
  docker rmi ${INSTANCE}-frontend:latest 2>/dev/null || true
done

docker builder prune -af

for INSTANCE in salon-x restaurant-x health-club-x nbne; do
  echo ""
  echo "=== Building $INSTANCE frontend ==="
  cd /opt/nbne/instances/$INSTANCE
  docker compose -p $INSTANCE --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml build --no-cache --build-arg CACHEBUST=middleware-fix frontend
  echo "=== Starting $INSTANCE frontend ==="
  docker compose -p $INSTANCE --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml up -d frontend
  echo "=== $INSTANCE DONE ==="
done

sleep 5

echo ""
echo "=== Testing auth endpoint on all instances ==="
for PORT in 3001 3002 3003 3004; do
  echo -n "Port $PORT: "
  curl -s -X POST -H 'Content-Type: application/json' -d '{"username":"test","password":"test"}' http://127.0.0.1:$PORT/api/auth | head -c 100
  echo ""
done

echo ""
echo "=== ALL REBUILDS COMPLETE ==="

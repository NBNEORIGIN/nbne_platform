#!/bin/bash
set -e

echo "=== Rebuilding remaining 3 frontends ==="

for INSTANCE in restaurant-x health-club-x nbne; do
  echo "--- Stopping $INSTANCE frontend ---"
  cd /opt/nbne/instances/$INSTANCE
  docker compose -p $INSTANCE --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml stop frontend 2>/dev/null || true
  docker compose -p $INSTANCE --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml rm -f frontend 2>/dev/null || true
  docker rmi ${INSTANCE}-frontend:latest 2>/dev/null || true
done

docker builder prune -af

for INSTANCE in restaurant-x health-club-x nbne; do
  echo ""
  echo "=== Building $INSTANCE frontend ==="
  cd /opt/nbne/instances/$INSTANCE
  docker compose -p $INSTANCE --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml build --no-cache --build-arg CACHEBUST=portal-rename frontend
  echo "=== Starting $INSTANCE frontend ==="
  docker compose -p $INSTANCE --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml up -d frontend
  echo "=== $INSTANCE DONE ==="
done

echo ""
echo "=== ALL REBUILDS COMPLETE ==="

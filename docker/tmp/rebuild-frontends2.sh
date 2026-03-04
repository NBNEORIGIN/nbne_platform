#!/bin/bash
set -euo pipefail

cd /opt/nbne/shared
git pull origin main

COMPOSE="/opt/nbne/shared/docker/docker-compose.client.yml"

for SLUG in salon-x restaurant-x health-club-x nbne; do
  echo "=== Rebuilding $SLUG frontend ==="
  DIR="/opt/nbne/instances/$SLUG"
  cd "$DIR"
  docker compose --env-file .env -f "$COMPOSE" -p "$SLUG" up -d --build --no-deps frontend
  echo "  $SLUG frontend rebuilt"
done

echo ""
echo "All frontends rebuilt."
docker ps --format "table {{.Names}}\t{{.Status}}" | grep frontend
echo "REBUILD_DONE"

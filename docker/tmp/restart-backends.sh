#!/bin/bash
set -e

for INST in salon-x restaurant-x health-club-x nbne; do
  cd /opt/nbne/instances/$INST
  docker compose -p $INST --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml restart backend
  echo "$INST backend restarted"
done

echo "ALL BACKENDS RESTARTED"

#!/bin/bash
set -e
cd /opt/nbne/repo

echo "=== Pulling latest code ==="
git pull origin main

echo "=== Rebuilding salon-x frontend ==="
cd /opt/nbne/instances/salon-x
docker compose -f /opt/nbne/shared/docker/docker-compose.client.yml build --no-cache frontend
docker compose -f /opt/nbne/shared/docker/docker-compose.client.yml up -d frontend
echo "salon-x frontend rebuilt and restarted"

echo "=== Rebuilding restaurant-x frontend ==="
cd /opt/nbne/instances/restaurant-x
docker compose -f /opt/nbne/shared/docker/docker-compose.client.yml build --no-cache frontend
docker compose -f /opt/nbne/shared/docker/docker-compose.client.yml up -d frontend
echo "restaurant-x frontend rebuilt and restarted"

echo "=== Rebuilding health-club-x frontend ==="
cd /opt/nbne/instances/health-club-x
docker compose -f /opt/nbne/shared/docker/docker-compose.client.yml build --no-cache frontend
docker compose -f /opt/nbne/shared/docker/docker-compose.client.yml up -d frontend
echo "health-club-x frontend rebuilt and restarted"

echo "=== Rebuilding nbne frontend ==="
cd /opt/nbne/instances/nbne
docker compose -f /opt/nbne/shared/docker/docker-compose.client.yml build --no-cache frontend
docker compose -f /opt/nbne/shared/docker/docker-compose.client.yml up -d frontend
echo "nbne frontend rebuilt and restarted"

echo "=== All 4 frontends rebuilt ==="

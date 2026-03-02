#!/bin/bash
# Deploy latest code to all client instances
# Usage: ./deploy.sh [slug]   — deploy single client
#        ./deploy.sh           — deploy all clients

set -euo pipefail

BASE_DIR="/opt/nbne"
SHARED_DIR="$BASE_DIR/shared"
COMPOSE_FILE="$BASE_DIR/shared/docker/docker-compose.client.yml"

# Pull latest code
echo "📥 Pulling latest code..."
cd "$SHARED_DIR"
git pull origin main

SINGLE="${1:-}"

deploy_instance() {
  local slug="$1"
  local dir="$BASE_DIR/instances/$slug"

  if [ ! -f "$dir/.env" ]; then
    echo "⚠️  Skipping $slug — no .env file"
    return
  fi

  echo "🔄 Deploying $slug..."
  cd "$dir"
  docker compose --env-file .env \
    -f "$COMPOSE_FILE" \
    -p "$slug" \
    up -d --build --remove-orphans

  echo "  ✅ $slug deployed"
}

if [ -n "$SINGLE" ]; then
  deploy_instance "$SINGLE"
else
  for dir in "$BASE_DIR/instances"/*/; do
    slug=$(basename "$dir")
    deploy_instance "$slug"
  done
fi

echo ""
echo "✅ Deployment complete"

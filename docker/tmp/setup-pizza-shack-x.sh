#!/bin/bash
# Deploy Pizza Shack X demo instance
# Run on Hetzner server: bash /opt/nbne/shared/docker/tmp/setup-pizza-shack-x.sh
#
# Prerequisites:
#   1. Server already set up with /opt/nbne/shared (git repo)
#   2. DNS: pizza-shack-x.nbne.uk → server IP (Cloudflare proxied)
#   3. Latest code pulled: cd /opt/nbne/shared && git pull origin main

set -euo pipefail

SLUG="pizza-shack-x"
DOMAIN="pizza-shack-x.nbne.uk"
FE_PORT=3007
BE_PORT=8007

echo "═══════════════════════════════════════════════"
echo "🍕 Setting up Pizza Shack X demo"
echo "═══════════════════════════════════════════════"

# Step 1: Pull latest code
echo "📥 Pulling latest code..."
cd /opt/nbne/shared
git pull origin main

# Step 2: Create instance via new-client.sh
if [ -d "/opt/nbne/instances/$SLUG" ]; then
  echo "⚠️  Instance already exists — redeploying..."
  cd /opt/nbne/instances/$SLUG
  docker compose --env-file .env \
    -f /opt/nbne/shared/docker/docker-compose.client.yml \
    -p "$SLUG" \
    up -d --build --remove-orphans
else
  echo "🔧 Creating new instance..."
  bash /opt/nbne/shared/docker/scripts/new-client.sh \
    "$SLUG" "$DOMAIN" "$FE_PORT" "$BE_PORT"
fi

echo ""
echo "═══════════════════════════════════════════════"
echo "✅ Pizza Shack X deployment complete!"
echo ""
echo "   🌐 https://$DOMAIN"
echo "   📱 https://$DOMAIN/order  (customer order page)"
echo "   🔥 https://$DOMAIN/admin/kitchen  (kitchen display)"
echo "   📊 https://$DOMAIN/admin/orders  (admin dashboard)"
echo ""
echo "   Login: pizza-shack-x-owner / admin123"
echo "          pizza-shack-x-staff1 / admin123"
echo ""
echo "   DNS: Point $DOMAIN A record → $(curl -s ifconfig.me 2>/dev/null || echo '<server-ip>')"
echo "   Cloudflare: Enable orange cloud proxy for SSL"
echo "═══════════════════════════════════════════════"

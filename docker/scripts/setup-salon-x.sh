#!/bin/bash
set -euo pipefail

# Generate secrets
DB_PASS=$(openssl rand -hex 16)
SEC_KEY=$(openssl rand -hex 32)

# Remove old .env and recreate
rm -f /opt/nbne/instances/salon-x/.env
mkdir -p /opt/nbne/instances/salon-x

cat > /opt/nbne/instances/salon-x/.env <<EOF
CLIENT_SLUG=salon-x
DOMAIN=salon-x.nbne.uk
FRONTEND_PORT=3001
BACKEND_PORT=8001
DB_PASSWORD=${DB_PASS}
SECRET_KEY=${SEC_KEY}
EMAIL_USER=toby@nbnesigns.com
EMAIL_PASSWORD=
REMINDER_EMAIL_USER=toby@nbnesigns.com
REMINDER_EMAIL_PASSWORD=
REMINDER_FROM_EMAIL=toby@nbnesigns.com
R2_ACCESS_KEY_ID=H0GXfvz29XtAbmaJSjfqehm5AfYVig6XAHbWNPWD
R2_SECRET_ACCESS_KEY=65e1a0f773a40de988a66379f9db0cb43937c417145f4a673257f12d56f61bd9
R2_ENDPOINT_URL=https://5551fa1ba3cec479fd938b41b642e9.r2.cloudflarestorage.com
R2_PUBLIC_URL=https://pub-0a37d1fed9c043aab8f7180d8b112489.r2.dev
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
OPENAI_API_KEY=
RESEND_API_KEY=
RESEND_FROM_EMAIL=onboarding@resend.dev
EOF

echo "salon-x .env created with secrets"
grep -E '^(DB_PASSWORD|SECRET_KEY)' /opt/nbne/instances/salon-x/.env

# Start the instance
cd /opt/nbne/instances/salon-x
docker compose --env-file .env \
  -f /opt/nbne/shared/docker/docker-compose.client.yml \
  -p salon-x \
  up -d --build

echo "salon-x instance starting..."
sleep 10
docker compose -p salon-x ps

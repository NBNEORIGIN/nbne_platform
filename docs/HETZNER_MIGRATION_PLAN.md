# Hetzner Cloud Migration Plan

## Current Architecture (Vercel + Railway)

```
DNS (Cloudflare / Registrar)
  │
  ├── business.nbne.uk ──────────► Vercel (nbne-landing)
  ├── salon-x2.vercel.app ───────► Vercel (nbne-business) ──┐
  ├── tavola-gray.vercel.app ────► Vercel (restaurant-x) ──┤
  ├── nbne-business-health-club-x► Vercel (health-club-x) ─┤
  ├── nbne-business-nbne ────────► Vercel (nbne) ──────────┤
  └── nbne-business-mind-dept ───► Vercel (mind-dept) ─────┤
                                                             │
  Each Vercel project:                                       │
   - Runs Next.js (SSR + static)                             │
   - Has /api/django/* proxy route ──────────────────────────┤
   - Env vars: NEXT_PUBLIC_TENANT_SLUG, DJANGO_BACKEND_URL   │
                                                             │
  Railway (single backend) ◄─────────────────────────────────┘
   - Django/Gunicorn on port 8000
   - PostgreSQL (shared, all tenants)
   - R2 for media uploads
   - start.sh: migrate + seed + gunicorn
```

### How the proxy works today

1. Browser hits `salon-x2.vercel.app/api/django/bookings/`
2. Next.js API route `/api/django/[...path]/route.ts` catches it
3. Reads `DJANGO_BACKEND_URL` env var (e.g. `https://nbneplatform-production.up.railway.app`)
4. Reads `NEXT_PUBLIC_TENANT_SLUG` env var (e.g. `salon-x`)
5. Forwards to `{DJANGO_BACKEND_URL}/api/bookings/?tenant=salon-x` with `X-Tenant-Slug: salon-x` header
6. Returns Django response to browser

Key point: the browser **never** talks to Railway directly. All API calls go through `/api/django/*` on the Vercel domain.

### Current monthly cost: ~$223

- Vercel Pro: $20 base + $193 overages (mostly build minutes)
- Railway: ~$10

---

## Target Architecture (Hetzner Cloud)

```
Cloudflare (DNS + CDN + SSL)
  │
  ├── nefireandmedical.co.uk ─────┐
  ├── salon-x.nbne.uk ───────────┤
  ├── tavola.nbne.uk ────────────┤
  ├── fithub.nbne.uk ────────────┤
  ├── app.nbnesigns.co.uk ───────┤  A records → Hetzner IP
  ├── business.nbne.uk ──────────┤
  └── minddepartment.nbne.uk ───┤
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────┐
│  Hetzner CX41 (4 vCPU, 16GB RAM, €15.49/mo)             │
│  Ubuntu 24.04 LTS                                         │
│  IP: xxx.xxx.xxx.xxx                                      │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Nginx (reverse proxy + SSL via Cloudflare Origin)   │  │
│  │                                                     │  │
│  │  Per-client vhost:                                  │  │
│  │   salon-x.nbne.uk      → frontend:3001 / api:8001  │  │
│  │   tavola.nbne.uk       → frontend:3002 / api:8002  │  │
│  │   fithub.nbne.uk       → frontend:3003 / api:8003  │  │
│  │   app.nbnesigns.co.uk  → frontend:3004 / api:8004  │  │
│  │   minddept.nbne.uk     → frontend:3005 / api:8005  │  │
│  │   nefireandmedical.co.uk→ frontend:3006 / api:8006  │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  Docker Compose per client instance:                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         │
│  │ Instance A  │ │ Instance B  │ │ Instance C  │  ...     │
│  │ frontend    │ │ frontend    │ │ frontend    │         │
│  │ backend     │ │ backend     │ │ backend     │         │
│  │ postgres    │ │ postgres    │ │ postgres    │         │
│  └─────────────┘ └─────────────┘ └─────────────┘         │
│                                                           │
│  Shared:                                                  │
│  - R2 for media (keep existing, basically free)           │
│  - IONOS SMTP for emails (already configured)             │
│  - Cloudflare for DNS/CDN/SSL                             │
└──────────────────────────────────────────────────────────┘
```

### Target monthly cost: ~€20-30

- Hetzner CX41: €15.49/mo
- Cloudflare: Free (proxy + SSL + CDN)
- R2 media: ~free (existing)
- Domains: ~£4-10/year each
- **Total: ~€20/mo** (vs $223/mo)

---

## How the Proxy Changes

### Current: Next.js serverless proxy route (Vercel)

```
Browser → Vercel Edge → /api/django/[...path]/route.ts → Railway Django
```

The proxy exists because:
1. Vercel injects stale `x-tenant-slug` headers
2. Chrome CORS strips custom headers on cross-origin requests
3. Need to inject tenant slug from env var

### New: Nginx handles the proxy directly

```
Browser → Cloudflare → Nginx → Next.js (pages) or Django (API)
```

Nginx routes based on path:
- `/api/*` → Django backend (same instance)
- Everything else → Next.js frontend

```nginx
# /etc/nginx/sites-enabled/salon-x.conf
server {
    listen 443 ssl;
    server_name salon-x.nbne.uk;

    ssl_certificate     /etc/ssl/cloudflare/origin.pem;
    ssl_certificate_key /etc/ssl/cloudflare/origin-key.pem;

    # API requests → Django backend
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Tenant-Slug salon-x;
    }

    # Media files → R2 (or local)
    location /media/ {
        proxy_pass https://pub-0a37d1fed9c043aab8f7180d8b112489.r2.dev/;
    }

    # Everything else → Next.js
    location / {
        proxy_pass http://127.0.0.1:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Key change:** The Next.js proxy route (`/api/django/[...path]`) is **no longer needed**. Nginx handles path-based routing directly. The browser calls `/api/bookings/` and Nginx forwards it to Django — no serverless function in the middle.

### Frontend code change required

`frontend/lib/api.ts` currently uses:
```ts
const API_BASE = '/api/django'
```

This needs to change to:
```ts
const API_BASE = '/api'
```

Since Nginx routes `/api/*` directly to Django, the `/api/django` prefix is unnecessary. The Next.js proxy routes can be removed entirely.

---

## Per-Client Docker Setup

### Directory structure on server

```
/opt/nbne/
├── shared/                     # Shared repo clone
│   ├── frontend/
│   ├── backend/
│   └── docker/
│       ├── Dockerfile.frontend
│       ├── Dockerfile.backend
│       └── docker-compose.template.yml
├── instances/
│   ├── salon-x/
│   │   ├── .env                # Client-specific env vars
│   │   └── docker-compose.yml  # Generated from template
│   ├── mind-department/
│   │   ├── .env
│   │   └── docker-compose.yml
│   └── ne-fire-medical/
│       ├── .env
│       └── docker-compose.yml
├── nginx/
│   ├── nginx.conf
│   └── sites/
│       ├── salon-x.conf
│       ├── mind-department.conf
│       └── ne-fire-medical.conf
├── backups/                    # Daily pg_dump per client
└── scripts/
    ├── deploy.sh               # Pull + rebuild + restart
    ├── new-client.sh           # Spin up new client instance
    └── backup.sh               # Daily backup script
```

### Dockerfile.frontend

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

Note: Requires `output: 'standalone'` in next.config.js.

### Dockerfile.backend

```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
RUN python manage.py collectstatic --noinput || true
EXPOSE 8000
CMD ["bash", "start.sh"]
```

### docker-compose.template.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${CLIENT_SLUG}
      POSTGRES_USER: nbne
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nbne -d ${CLIENT_SLUG}"]
      interval: 10s
      retries: 5

  backend:
    build:
      context: /opt/nbne/shared
      dockerfile: docker/Dockerfile.backend
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgres://nbne:${DB_PASSWORD}@db:5432/${CLIENT_SLUG}
      SECRET_KEY: ${SECRET_KEY}
      DEBUG: "False"
      ALLOWED_HOSTS: ${DOMAIN},localhost
      CORS_ALLOWED_ORIGINS: https://${DOMAIN}
      CSRF_TRUSTED_ORIGINS: https://${DOMAIN}
      SEED_TENANT: ${CLIENT_SLUG}
      # Email
      EMAIL_HOST: smtp.ionos.co.uk
      EMAIL_PORT: 587
      EMAIL_HOST_USER: ${EMAIL_USER}
      EMAIL_HOST_PASSWORD: ${EMAIL_PASSWORD}
      DEFAULT_FROM_EMAIL: ${EMAIL_USER}
      # R2 media storage
      R2_ACCESS_KEY_ID: ${R2_ACCESS_KEY_ID}
      R2_SECRET_ACCESS_KEY: ${R2_SECRET_ACCESS_KEY}
      R2_ENDPOINT_URL: ${R2_ENDPOINT_URL}
      R2_PUBLIC_URL: ${R2_PUBLIC_URL}
      # Stripe (per-client)
      STRIPE_SECRET_KEY: ${STRIPE_SECRET_KEY}
      STRIPE_WEBHOOK_SECRET: ${STRIPE_WEBHOOK_SECRET}
      FRONTEND_URL: https://${DOMAIN}
      # OpenAI
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    ports:
      - "${BACKEND_PORT}:8000"

  frontend:
    build:
      context: /opt/nbne/shared
      dockerfile: docker/Dockerfile.frontend
      args:
        NEXT_PUBLIC_TENANT_SLUG: ${CLIENT_SLUG}
        NEXT_PUBLIC_API_BASE_URL: https://${DOMAIN}
    restart: unless-stopped
    environment:
      NEXT_PUBLIC_TENANT_SLUG: ${CLIENT_SLUG}
      DJANGO_BACKEND_URL: http://backend:8000
    ports:
      - "${FRONTEND_PORT}:3000"

volumes:
  pgdata:
```

### Per-client .env

```bash
# /opt/nbne/instances/ne-fire-medical/.env
CLIENT_SLUG=ne-fire-medical
DOMAIN=nefireandmedical.co.uk
FRONTEND_PORT=3006
BACKEND_PORT=8006
DB_PASSWORD=<generated-random>
SECRET_KEY=<generated-random>
EMAIL_USER=toby@nbnesigns.com
EMAIL_PASSWORD=!49Monkswood
R2_ACCESS_KEY_ID=H0GXfvz29XtAbmaJSjfqehm5AfYVig6XAHbWNPWD
R2_SECRET_ACCESS_KEY=<key>
R2_ENDPOINT_URL=https://5551fa1ba3cec479fd938b41b642e9.r2.cloudflarestorage.com
R2_PUBLIC_URL=https://pub-0a37d1fed9c043aab8f7180d8b112489.r2.dev
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
OPENAI_API_KEY=
```

---

## New Client Script

```bash
#!/bin/bash
# /opt/nbne/scripts/new-client.sh
# Usage: ./new-client.sh ne-fire-medical nefireandmedical.co.uk 3006 8006

SLUG=$1
DOMAIN=$2
FE_PORT=$3
BE_PORT=$4
DIR="/opt/nbne/instances/$SLUG"

mkdir -p "$DIR"

# Generate secrets
DB_PASS=$(openssl rand -hex 16)
SECRET=$(openssl rand -hex 32)

# Create .env
cat > "$DIR/.env" <<EOF
CLIENT_SLUG=$SLUG
DOMAIN=$DOMAIN
FRONTEND_PORT=$FE_PORT
BACKEND_PORT=$BE_PORT
DB_PASSWORD=$DB_PASS
SECRET_KEY=$SECRET
EMAIL_USER=toby@nbnesigns.com
EMAIL_PASSWORD=!49Monkswood
R2_ACCESS_KEY_ID=H0GXfvz29XtAbmaJSjfqehm5AfYVig6XAHbWNPWD
R2_SECRET_ACCESS_KEY=65e1a0f773a40de988a66379f9db0cb43937c417145f4a673257f12d56f61bd9
R2_ENDPOINT_URL=https://5551fa1ba3cec479fd938b41b642e9.r2.cloudflarestorage.com
R2_PUBLIC_URL=https://pub-0a37d1fed9c043aab8f7180d8b112489.r2.dev
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
OPENAI_API_KEY=
EOF

# Copy compose template
cp /opt/nbne/shared/docker/docker-compose.template.yml "$DIR/docker-compose.yml"

# Generate Nginx config
cat > "/etc/nginx/sites-enabled/$SLUG.conf" <<EOF
server {
    listen 443 ssl;
    server_name $DOMAIN;
    ssl_certificate     /etc/ssl/cloudflare/origin.pem;
    ssl_certificate_key /etc/ssl/cloudflare/origin-key.pem;

    client_max_body_size 50M;

    location /api/ {
        proxy_pass http://127.0.0.1:$BE_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Tenant-Slug $SLUG;
    }

    location /media/ {
        proxy_pass https://pub-0a37d1fed9c043aab8f7180d8b112489.r2.dev/;
    }

    location / {
        proxy_pass http://127.0.0.1:$FE_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Start instance
cd "$DIR"
docker compose --env-file .env up -d --build

# Reload Nginx
nginx -t && systemctl reload nginx

echo "✅ Client $SLUG is live at https://$DOMAIN"
echo "   Frontend: http://localhost:$FE_PORT"
echo "   Backend:  http://localhost:$BE_PORT"
```

---

## Deploy Script (Updates)

```bash
#!/bin/bash
# /opt/nbne/scripts/deploy.sh
# Pull latest code and rebuild all instances

cd /opt/nbne/shared
git pull origin main

# Rebuild images (shared build, fast due to Docker layer caching)
docker compose -f docker/docker-compose.build.yml build

# Rolling restart each instance
for dir in /opt/nbne/instances/*/; do
    SLUG=$(basename "$dir")
    echo "Deploying $SLUG..."
    cd "$dir"
    docker compose --env-file .env up -d --build --remove-orphans
    echo "  ✅ $SLUG restarted"
done

echo "All instances deployed."
```

---

## Backup Script

```bash
#!/bin/bash
# /opt/nbne/scripts/backup.sh
# Run via cron: 0 3 * * * /opt/nbne/scripts/backup.sh

BACKUP_DIR="/opt/nbne/backups/$(date +%Y-%m-%d)"
mkdir -p "$BACKUP_DIR"

for dir in /opt/nbne/instances/*/; do
    SLUG=$(basename "$dir")
    source "$dir/.env"
    
    CONTAINER="${SLUG}-db-1"
    docker exec "$CONTAINER" pg_dump -U nbne "$SLUG" | gzip > "$BACKUP_DIR/${SLUG}.sql.gz"
    echo "✅ Backed up $SLUG"
done

# Keep 30 days of backups
find /opt/nbne/backups -maxdepth 1 -mtime +30 -type d -exec rm -rf {} \;

echo "Backups complete: $BACKUP_DIR"
```

---

## Code Changes Required

### 1. Next.js standalone output

```js
// frontend/next.config.js — add output: 'standalone'
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  // ... rest of config
}
```

### 2. API base URL change

```ts
// frontend/lib/api.ts
// Change from:
const API_BASE = '/api/django'
// To:
const API_BASE = '/api'
```

Since Nginx routes `/api/*` → Django directly, the `/api/django` prefix is no longer needed.

### 3. Remove proxy routes (optional, but cleaner)

The following files become unnecessary since Nginx handles the proxy:
- `frontend/app/api/django/[...path]/route.ts`
- `frontend/app/api/v2/[...path]/route.ts`

However, **keep them for now** as a fallback during transition. They'll still work — just unused.

### 4. Auth route changes

`frontend/app/api/auth/route.ts` currently proxies login to Django. On Hetzner, the frontend container can reach the backend container directly via Docker networking (`http://backend:8000`), so `DJANGO_BACKEND_URL=http://backend:8000` still works. **No change needed.**

### 5. Middleware — no changes needed

The middleware reads `NEXT_PUBLIC_TENANT_SLUG` from env vars and does JWT validation. This works identically in Docker. **No change needed.**

---

## Migration Steps

### Phase 1: Server Setup (~1 hour)

1. Create Hetzner CX41 (4 vCPU, 16GB RAM, 160GB SSD)
2. Ubuntu 24.04 LTS, SSH key auth
3. Install: Docker, Docker Compose, Nginx
4. Configure firewall (UFW): allow 80, 443, 22 only
5. Set up Cloudflare Origin Certificate for SSL

### Phase 2: Code Prep (~30 min)

1. Add `output: 'standalone'` to next.config.js
2. Change `API_BASE` from `/api/django` to `/api`
3. Create Dockerfiles and compose template
4. Create deploy/backup/new-client scripts
5. Test Docker build locally

### Phase 3: Demo Sites Migration (~1 hour)

1. Spin up salon-x, restaurant-x, health-club-x, nbne instances
2. Export PostgreSQL from Railway: `pg_dump` → import to Docker Postgres
3. Verify each site works
4. Update DNS to point to Hetzner (via Cloudflare proxy)
5. Keep Railway running in parallel for 48 hours

### Phase 4: Mind Department Migration (~30 min, CAREFUL)

1. This is a LIVE CLIENT — schedule a maintenance window
2. Export their PostgreSQL data
3. Spin up mind-department instance
4. Verify thoroughly
5. Switch DNS
6. Monitor for 24 hours

### Phase 5: First New Client — NE Fire & Medical (~30 min)

1. Run `./new-client.sh ne-fire-medical nefireandmedical.co.uk 3006 8006`
2. Configure their DNS
3. Set up their data (courses, products, etc.)

### Phase 6: Decommission (~15 min)

1. Cancel Railway subscription
2. Downgrade Vercel to free tier (or cancel)
3. Remove old DNS records

---

## Resource Budget (CX41, 16GB RAM)

| Per Instance | RAM | CPU |
|---|---|---|
| PostgreSQL | ~100MB | Minimal |
| Django/Gunicorn (4 workers) | ~200MB | Light |
| Next.js (standalone) | ~150MB | Light |
| **Total per client** | **~450MB** | |
| Nginx (shared) | ~50MB | |
| OS overhead | ~500MB | |
| **Available for clients** | **~15GB** | |
| **Max clients on CX41** | **~30** | |

You can comfortably run 10-15 clients with headroom on a CX41. Beyond 20, upgrade to CX51 (32GB, €29/mo).

---

## Monitoring

- **Uptime:** Use Cloudflare health checks (free) or UptimeRobot (free tier)
- **Logs:** `docker logs <container>` or centralize with Loki/Grafana (optional)
- **Disk:** Set up alert at 80% with `df` cron check
- **Backups:** Daily pg_dump + 30-day retention

---

## Timeline

| Phase | Time | Blocker |
|---|---|---|
| Server setup | 1 hour | None |
| Code prep | 30 min | None |
| Demo sites | 1 hour | Railway DB export |
| Mind Department | 30 min | Schedule with client |
| NE Fire & Medical | 30 min | Waiting on Ian's assets |
| Decommission | 15 min | After 48hr parallel run |
| **Total** | **~4 hours** | |

---

## Risk Mitigation

| Risk | Mitigation |
|---|---|
| Server goes down | Hetzner snapshots (€0.01/GB/mo), daily backups to R2 |
| Disk failure | Hetzner has redundant storage; daily off-site backups |
| DDoS | Cloudflare proxy handles this (free tier) |
| Security patches | unattended-upgrades for Ubuntu; Docker images pinned |
| Need to scale | Hetzner upgrade takes 2 min (live resize); or add second server |
| Rollback | Keep Railway + Vercel running for 48 hours after migration |

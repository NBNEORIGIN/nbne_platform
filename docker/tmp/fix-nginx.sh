#!/bin/bash
set -e

# Fix all 4 Nginx configs to route /api/auth and /api/django/ to Next.js frontend
# instead of Django backend

declare -A BACKEND_PORTS
BACKEND_PORTS[salon-x]=8001
BACKEND_PORTS[restaurant-x]=8002
BACKEND_PORTS[health-club-x]=8003
BACKEND_PORTS[nbne]=8004

declare -A FRONTEND_PORTS
FRONTEND_PORTS[salon-x]=3001
FRONTEND_PORTS[restaurant-x]=3002
FRONTEND_PORTS[health-club-x]=3003
FRONTEND_PORTS[nbne]=3004

declare -A DOMAINS
DOMAINS[salon-x]="salon-x.nbne.uk"
DOMAINS[restaurant-x]="tavola.nbne.uk"
DOMAINS[health-club-x]="fithub.nbne.uk"
DOMAINS[nbne]="app.nbne.uk"

declare -A SLUGS
SLUGS[salon-x]="salon-x"
SLUGS[restaurant-x]="restaurant-x"
SLUGS[health-club-x]="health-club-x"
SLUGS[nbne]="nbne"

declare -A COMMENTS
COMMENTS[salon-x]="salon-x — salon-x.nbne.uk"
COMMENTS[restaurant-x]="restaurant-x — tavola.nbne.uk"
COMMENTS[health-club-x]="health-club-x — fithub.nbne.uk"
COMMENTS[nbne]="nbne — app.nbne.uk"

for INSTANCE in salon-x restaurant-x health-club-x nbne; do
  BP=${BACKEND_PORTS[$INSTANCE]}
  FP=${FRONTEND_PORTS[$INSTANCE]}
  DOM=${DOMAINS[$INSTANCE]}
  SLUG=${SLUGS[$INSTANCE]}
  COMMENT=${COMMENTS[$INSTANCE]}
  CONF="/etc/nginx/sites-enabled/${INSTANCE}.conf"

  cat > "$CONF" <<ENDCONF
# ${COMMENT}
server {
    listen 443 ssl http2;
    server_name ${DOM};

    ssl_certificate     /etc/ssl/cloudflare/origin.pem;
    ssl_certificate_key /etc/ssl/cloudflare/origin-key.pem;

    client_max_body_size 50M;

    # Django admin static files
    location /static/ {
        proxy_pass http://127.0.0.1:${BP};
        proxy_set_header Host \$host;
    }

    # Next.js API routes -> frontend (must be before /api/)
    location /api/auth {
        proxy_pass http://127.0.0.1:${FP};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /api/django/ {
        proxy_pass http://127.0.0.1:${FP};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # API -> Django backend
    location /api/ {
        proxy_pass http://127.0.0.1:${BP};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Tenant-Slug ${SLUG};
    }

    # Django admin panel (moved to /django-admin/ to free /admin for Next.js)
    location /django-admin/ {
        proxy_pass http://127.0.0.1:${BP};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Media files -> R2 public URL
    location /media/ {
        proxy_pass https://pub-0a37d1fed9c043aab8f7180d8b112489.r2.dev/;
    }

    # Everything else -> Next.js frontend
    location / {
        proxy_pass http://127.0.0.1:${FP};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# HTTP -> HTTPS redirect
server {
    listen 80;
    server_name ${DOM};
    return 301 https://\$host\$request_uri;
}
ENDCONF

  echo "$INSTANCE config written"
done

nginx -t && nginx -s reload && echo "Nginx reloaded OK"

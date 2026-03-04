#!/bin/bash
set -e

cat > /etc/nginx/sites-enabled/floe.conf << 'NGINX'
server {
    listen 443 ssl http2;
    server_name floe.nbne.uk;

    ssl_certificate     /etc/ssl/cloudflare/origin.pem;
    ssl_certificate_key /etc/ssl/cloudflare/origin-key.pem;

    root /opt/nbne/floe-landing;
    index index.html;

    # Serve platform.html at /platform
    location = /platform {
        try_files /platform.html =404;
    }

    # SPA-style fallback — all other routes serve index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}

# HTTP -> HTTPS redirect
server {
    listen 80;
    server_name floe.nbne.uk;
    return 301 https://$host$request_uri;
}
NGINX

echo "floe.conf written"
nginx -t && nginx -s reload && echo "Nginx reloaded OK"

echo ""
echo "=== Verify ==="
curl -s -k -H 'Host: floe.nbne.uk' https://127.0.0.1/ | head -5
echo ""
echo "=== DONE ==="

#!/bin/bash
set -e

echo "=== 1. Check existing Nginx configs ==="
ls /etc/nginx/sites-enabled/

echo ""
echo "=== 2. Check SSL certs ==="
ls /etc/letsencrypt/live/ 2>/dev/null || echo "No letsencrypt certs"
ls /etc/ssl/certs/cloudflare* 2>/dev/null || echo "No cloudflare certs"
# Check if existing sites use a shared cert
head -20 /etc/nginx/sites-enabled/salon-x.conf 2>/dev/null | grep ssl_certificate

echo ""
echo "=== 3. Copy landing site files ==="
mkdir -p /opt/nbne/floe-landing
cp /opt/nbne/shared/docker/tmp/floe-index.html /opt/nbne/floe-landing/index.html 2>/dev/null || echo "Will need to copy files"
ls -la /opt/nbne/floe-landing/ 2>/dev/null || echo "Dir not yet created"

echo ""
echo "=== DONE ==="

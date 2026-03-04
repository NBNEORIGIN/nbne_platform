#!/bin/bash
# Test auth endpoint directly from server, avoiding any PowerShell quoting issues

echo "=== Test 1: Direct to Django backend ==="
curl -s -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Slug: salon-x' \
  -d '{"username":"owner@salon-x.demo","password":"admin123"}' \
  http://127.0.0.1:8001/api/auth/login/ | head -c 500
echo ""

echo "=== Test 2: Direct to Next.js frontend ==="
curl -s -X POST \
  -H 'Content-Type: application/json' \
  -d '{"username":"owner@salon-x.demo","password":"admin123"}' \
  http://127.0.0.1:3001/api/auth | head -c 500
echo ""

echo "=== Test 3: Through Nginx (HTTPS) ==="
curl -s -k -X POST \
  -H 'Content-Type: application/json' \
  -H 'Host: salon-x.nbne.uk' \
  -d '{"username":"owner@salon-x.demo","password":"admin123"}' \
  https://127.0.0.1/api/auth | head -c 500
echo ""

echo "=== DONE ==="

#!/bin/bash
echo "=== Test 1: Next.js auth (direct) ==="
curl -s -X POST \
  -H 'Content-Type: application/json' \
  -d '{"username":"owner@salon-x.demo","password":"admin123"}' \
  http://127.0.0.1:3001/api/auth | head -c 200
echo ""

echo "=== Test 2: Through Nginx (HTTPS) ==="
curl -s -k -X POST \
  -H 'Content-Type: application/json' \
  -H 'Host: salon-x.nbne.uk' \
  -d '{"username":"owner@salon-x.demo","password":"admin123"}' \
  https://127.0.0.1/api/auth | head -c 200
echo ""

echo "=== Test 3: /admin page via Nginx (should return Next.js HTML) ==="
curl -s -k -H 'Host: salon-x.nbne.uk' https://127.0.0.1/admin | head -c 200
echo ""

echo "=== DONE ==="

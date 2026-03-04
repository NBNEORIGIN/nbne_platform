#!/bin/bash
set -e

echo "=== Docker manual frontend build for salon-x ==="

# Run build inside a node container with source mounted
docker run --rm \
  -v /opt/nbne/shared/frontend:/src:ro \
  -e NEXT_PUBLIC_TENANT_SLUG=salon-x \
  -e NEXT_PUBLIC_API_PREFIX=/api \
  -w /app \
  node:20-alpine sh -c '
    set -e
    echo "--- Copying source ---"
    cp -r /src/* /src/.* . 2>/dev/null || true
    
    echo "--- Verifying page.tsx ---"
    cat app/page.tsx
    echo "---"
    head -5 app/home-page.tsx
    echo "---"
    head -5 app/app/layout.tsx
    
    echo "--- npm ci ---"
    npm ci --ignore-scripts 2>&1 | tail -3
    
    echo "--- npm run build ---"
    npm run build 2>&1 | tail -40
    
    echo ""
    echo "=== BUILD OUTPUT ANALYSIS ==="
    echo "Root page.js content:"
    cat .next/server/app/page.js
    echo ""
    echo "---"
    echo "Client chunk for root page:"
    ls .next/static/chunks/app/page-*.js 2>/dev/null
    cat .next/static/chunks/app/page-*.js | head -c 1000
    echo ""
    echo "---"
    echo "Searching for HomePageClient:"
    grep -rl "HomePageClient" .next/ 2>/dev/null | head -5 || echo "NOT FOUND anywhere"
    echo "---"
    echo "Searching for salon content in root chunk:"
    grep -c "Where style meets confidence" .next/static/chunks/app/page-*.js 2>/dev/null && echo "FOUND - salon page IS in root chunk" || echo "NOT FOUND in root chunk"
    echo "---"
    echo "Searching for staff dashboard in root chunk:"
    grep -c "Loading dashboard" .next/static/chunks/app/page-*.js 2>/dev/null && echo "FOUND - staff dashboard IS in root chunk (BAD)" || echo "NOT FOUND in root chunk (GOOD)"
    echo ""
    echo "=== DONE ==="
  '

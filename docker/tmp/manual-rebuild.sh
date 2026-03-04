#!/bin/bash
set -e

echo "=== Manual frontend rebuild for salon-x ==="
cd /opt/nbne/shared/frontend

# Verify source files
echo "--- Checking source files ---"
head -3 app/page.tsx
echo "---"
head -3 app/home-page.tsx
echo "---"
head -3 app/app/layout.tsx

# Install deps
echo "=== Installing dependencies ==="
npm ci --ignore-scripts 2>&1 | tail -5

# Build
echo "=== Building Next.js ==="
NEXT_PUBLIC_TENANT_SLUG=salon-x NEXT_PUBLIC_API_PREFIX=/api npm run build 2>&1 | tail -40

# Check output
echo "=== Checking build output ==="
echo "Root page.js module tree:"
cat .next/server/app/page.js | tr ',' '\n' | grep -i 'page\|layout' | head -10
echo "---"
echo "Looking for HomePageClient in chunks:"
grep -rl 'HomePageClient' .next/ 2>/dev/null | head -5 || echo "NOT FOUND"
echo "---"
echo "Looking for Staff Portal in root page chunk:"
# Find the client chunk for root page
ls -la .next/static/chunks/app/page-*.js
cat .next/static/chunks/app/page-*.js | head -c 500
echo ""
echo "---"
echo "Looking for salon content in root page:"
grep -o 'Where style meets confidence' .next/static/chunks/app/page-*.js 2>/dev/null || echo "Salon content NOT in root page chunk"
grep -o 'Loading dashboard' .next/static/chunks/app/page-*.js 2>/dev/null || echo "Staff dashboard NOT in root page chunk (GOOD)"

echo ""
echo "=== MANUAL BUILD DONE ==="

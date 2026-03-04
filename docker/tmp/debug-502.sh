#!/bin/bash
set -e

echo "=== Backend container status ==="
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E 'backend|NAMES'

echo ""
echo "=== Backend logs (last 30 lines) ==="
docker logs salon-x-backend-1 --tail 30 2>&1

echo ""
echo "=== Test direct backend ==="
curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1:8001/api/ 2>/dev/null || echo "UNREACHABLE"

echo ""
echo "=== Check APPEND_SLASH in settings.py ==="
docker exec salon-x-backend-1 grep -n APPEND_SLASH /app/config/settings.py 2>/dev/null || echo "NOT FOUND in settings.py"

echo ""
echo "=== DONE ==="

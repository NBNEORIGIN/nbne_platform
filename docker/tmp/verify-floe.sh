#!/bin/bash
set -e

echo "=== 1. Files in /opt/nbne/floe-landing ==="
ls -la /opt/nbne/floe-landing/

echo ""
echo "=== 2. Nginx config ==="
cat /etc/nginx/sites-enabled/floe.conf

echo ""
echo "=== 3. Test with correct Host header ==="
curl -s -k -o /dev/null -w "HTTP %{http_code}" -H 'Host: floe.nbne.uk' https://127.0.0.1/
echo ""
curl -s -k -H 'Host: floe.nbne.uk' https://127.0.0.1/ | head -3
echo ""

echo ""
echo "=== 4. Test /platform ==="
curl -s -k -o /dev/null -w "HTTP %{http_code}" -H 'Host: floe.nbne.uk' https://127.0.0.1/platform
echo ""

echo ""
echo "=== 5. Check DNS (does floe.nbne.uk resolve?) ==="
dig +short floe.nbne.uk 2>/dev/null || host floe.nbne.uk 2>/dev/null || echo "DNS not resolving (may need Cloudflare setup)"

echo "=== DONE ==="

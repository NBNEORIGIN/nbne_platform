#!/bin/bash
set -e

echo "=== 1. Pull latest code ==="
cd /opt/nbne/shared && git pull origin main

echo ""
echo "=== 2. Update Nginx configs ==="
bash /opt/nbne/shared/docker/tmp/fix-nginx.sh

echo ""
echo "=== 3. Recreate backends with media volume ==="
for INST in salon-x restaurant-x health-club-x nbne; do
  cd /opt/nbne/instances/$INST
  docker compose -p $INST --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml up -d --no-deps --force-recreate backend
  echo "$INST backend recreated"
done

echo ""
echo "Waiting 8s for backends to start..."
sleep 8

echo ""
echo "=== 4. Verify media volume mounted ==="
docker exec salon-x-backend-1 ls -la /app/media/ 2>/dev/null && echo "Media dir exists" || echo "Media dir missing"
docker inspect salon-x-backend-1 --format '{{range .Mounts}}{{.Type}} {{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'

echo ""
echo "=== 5. Verify Django storage config ==="
docker exec salon-x-backend-1 python manage.py shell -c "
from django.conf import settings
print('MEDIA_ROOT:', settings.MEDIA_ROOT)
print('MEDIA_URL:', settings.MEDIA_URL)
from django.core.files.storage import default_storage
print('Storage backend:', default_storage.__class__.__name__)
"

echo ""
echo "=== 6. Test file write ==="
docker exec salon-x-backend-1 python manage.py shell -c "
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
path = default_storage.save('test_upload.txt', ContentFile(b'hello from storage test'))
print('Saved to:', path)
exists = default_storage.exists(path)
print('File exists:', exists)
if exists:
    default_storage.delete(path)
    print('Cleaned up test file')
"

echo ""
echo "=== ALL DONE ==="

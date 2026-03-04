#!/bin/bash
set -e

echo "=== 1. R2 env vars in salon-x .env ==="
grep -i R2_ /opt/nbne/instances/salon-x/.env 2>/dev/null || echo "No R2 vars found"

echo ""
echo "=== 2. Django storage settings ==="
docker exec salon-x-backend-1 python manage.py shell -c "
from django.conf import settings
print('DEFAULT_FILE_STORAGE:', getattr(settings, 'DEFAULT_FILE_STORAGE', 'NOT SET'))
print('STORAGES:', getattr(settings, 'STORAGES', {}).get('default', 'NOT SET'))
print('MEDIA_ROOT:', settings.MEDIA_ROOT)
print('MEDIA_URL:', settings.MEDIA_URL)
print('MEDIA_VOLUME_PATH:', getattr(settings, 'MEDIA_VOLUME_PATH', 'NOT SET'))
"

echo ""
echo "=== 3. Check if media dir exists in container ==="
docker exec salon-x-backend-1 ls -la /app/media/ 2>/dev/null || echo "No /app/media/ dir"
docker exec salon-x-backend-1 ls -la /data/media/ 2>/dev/null || echo "No /data/media/ dir"

echo ""
echo "=== 4. Check Docker volumes for salon-x ==="
docker inspect salon-x-backend-1 --format '{{json .Mounts}}' 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "Could not inspect mounts"

echo ""
echo "=== 5. Test upload endpoint (dry run — check if reachable) ==="
curl -s -o /dev/null -w "HTTP %{http_code}" -X POST \
  -H 'X-Tenant-Slug: salon-x' \
  http://127.0.0.1:8001/api/documents/create/
echo ""

echo ""
echo "=== 6. Check existing documents in DB ==="
docker exec salon-x-backend-1 python manage.py shell -c "
from documents.models import Document
total = Document.objects.count()
with_file = Document.objects.exclude(file='').exclude(file__isnull=True).count()
placeholders = Document.objects.filter(is_placeholder=True).count()
print(f'Total docs: {total}, With file: {with_file}, Placeholders: {placeholders}')
if with_file > 0:
    d = Document.objects.exclude(file='').first()
    print(f'  Sample: id={d.id} title={d.title} file={d.file.name} size={d.size_bytes}')
"

echo ""
echo "=== DONE ==="

#!/bin/bash
# Daily backup of all client PostgreSQL databases
# Usage: ./backup.sh
# Cron: 0 3 * * * /opt/nbne/scripts/backup.sh >> /var/log/nbne-backup.log 2>&1

set -euo pipefail

BASE_DIR="/opt/nbne"
BACKUP_DIR="$BASE_DIR/backups/$(date +%Y-%m-%d)"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

echo "$(date) — Starting backups to $BACKUP_DIR"

for dir in "$BASE_DIR/instances"/*/; do
  slug=$(basename "$dir")
  
  if [ ! -f "$dir/.env" ]; then
    echo "  ⚠️  Skipping $slug — no .env file"
    continue
  fi

  CONTAINER="${slug}-db-1"
  
  # Check container is running
  if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    echo "  ⚠️  Skipping $slug — db container not running"
    continue
  fi

  # Dump database
  docker exec "$CONTAINER" pg_dump -U nbne "$slug" 2>/dev/null | gzip > "$BACKUP_DIR/${slug}.sql.gz"
  SIZE=$(du -sh "$BACKUP_DIR/${slug}.sql.gz" | cut -f1)
  echo "  ✅ $slug — $SIZE"
done

# Prune old backups
find "$BASE_DIR/backups" -maxdepth 1 -mtime +${RETENTION_DAYS} -type d -exec rm -rf {} \;
echo "$(date) — Backups complete. Pruned backups older than ${RETENTION_DAYS} days."

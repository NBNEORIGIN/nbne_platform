#!/bin/bash
# Show status of all client instances
# Usage: ./status.sh

BASE_DIR="/opt/nbne"

printf "%-25s %-12s %-12s %-12s %-30s\n" "CLIENT" "FRONTEND" "BACKEND" "DATABASE" "DOMAIN"
printf "%-25s %-12s %-12s %-12s %-30s\n" "-------" "--------" "-------" "--------" "------"

for dir in "$BASE_DIR/instances"/*/; do
  slug=$(basename "$dir")
  
  if [ ! -f "$dir/.env" ]; then
    continue
  fi

  source "$dir/.env"

  fe_status="down"
  be_status="down"
  db_status="down"

  docker ps --format '{{.Names}}' | grep -q "^${slug}-frontend-1$" && fe_status="✅ up"
  docker ps --format '{{.Names}}' | grep -q "^${slug}-backend-1$" && be_status="✅ up"
  docker ps --format '{{.Names}}' | grep -q "^${slug}-db-1$" && db_status="✅ up"

  printf "%-25s %-12s %-12s %-12s %-30s\n" "$slug" "$fe_status" "$be_status" "$db_status" "$DOMAIN"
done

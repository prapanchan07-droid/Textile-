#!/bin/sh
# Backup the PostgreSQL database of the Docker stack to ./backups (run from the repository root).
# Restore steps are in docs/database.md. Take a backup before every migration.
set -eu
mkdir -p backups
out="backups/textile-$(date +%Y%m%d-%H%M%S).dump"
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$out"
test -s "$out" || { echo "backup is empty, something went wrong" >&2; rm -f "$out"; exit 1; }
echo "wrote $out"

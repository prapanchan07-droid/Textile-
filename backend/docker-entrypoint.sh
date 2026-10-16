#!/bin/sh
set -e
# Volumes created by older runs are owned by root; fix that, then drop privileges.
chown -R 10001:10001 /app/data /app/uploaded_reports
# Bring the schema to the latest revision before the API starts (additive and reversible; see docs/database.md).
if [ "${AUTO_MIGRATE:-true}" = "false" ]; then
  setpriv --reuid=10001 --regid=10001 --init-groups alembic upgrade head
fi
exec setpriv --reuid=10001 --regid=10001 --init-groups "$@"

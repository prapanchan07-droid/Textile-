#!/bin/sh
set -e
# Volumes created by older runs are owned by root; fix that, then drop privileges.
chown -R 10001:10001 /app/data /app/uploaded_reports
exec setpriv --reuid=10001 --regid=10001 --init-groups "$@"

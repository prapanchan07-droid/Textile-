# Database: PostgreSQL, migrations, backup and restore

The database is **PostgreSQL 16+** (JSONB, time-zone-aware timestamps). Tables are defined in
`backend/app/mill/models.py` (weaving platform) and `backend/app/models/user.py` (logins).

## Configuration

Settings come from environment variables (or `backend/.env`, which is git-ignored). Set **either**:

| Variable | Meaning |
|---|---|
| `DATABASE_URL` | Full URL, e.g. `postgresql+psycopg://textile:PASSWORD@localhost:5432/textile` |
| `POSTGRES_HOST` / `POSTGRES_PORT` / `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | Pieces; the app builds the URL and escapes the password. |

Other settings: `AUTO_MIGRATE` (run migrations at API start-up; `false` in Docker, where the entrypoint runs them),
`ENVIRONMENT` (`production` = no demo login), `UPLOAD_DIR` (where original report files are kept, default
`backend/uploaded_reports`), `MAX_UPLOAD_MB`, `BACKGROUND_JOBS_ENABLED`, `BACKGROUND_INTERVAL_SECONDS`,
`TELEMETRY_STALE_SECONDS`, `TELEMETRY_RETENTION_DAYS`.

## Schema

| Area | Tables |
|---|---|
| Machines | `looms` (TY/TS/SZ + number, manufacturer, model, width), `styles`, `machine_connections`, `telemetry_samples` |
| Imports | `import_batches` (file hash, status, counts, data-quality summary, reconciliation), `import_issues` (row-level), `raw_source_rows` (source cells) |
| Production | `shift_production` (unique per loom, date, shift, source; `data_origin`, `extras` for source-specific fields), `production_targets`, `energy_readings` |
| People and work | `people`, `groups`, `group_loom_assignments` and `group_member_assignments` (dated), `tasks`, `task_events`, `work_orders` |
| Alerts | `alert_rules`, `alerts`, `alert_events`, `notifications` |
| Reporting and audit | `owner_reports` (frozen `snapshot`), `audit_log`, `users` |

NULL means "not available in the source"; 0 means the source reported zero.

## Migrations (Alembic)

`backend/alembic/versions/0001_weaving_platform_schema.py` creates the whole schema. The migration chain was
restarted when the platform was rebuilt from scratch (October 2026), so **a database created by the earlier
application (revisions 0001–0003 of the old `wv_*` schema) must be dropped and recreated**, not upgraded:

```bash
psql -U postgres -c "DROP DATABASE textile WITH (FORCE)" -c "CREATE DATABASE textile OWNER textile"
cd backend && alembic upgrade head
```

Day-to-day:

```bash
cd backend
alembic upgrade head          # apply
alembic current               # where the database is
alembic check                 # fail if the models and migrations disagree
alembic revision --autogenerate -m "describe the change"   # then review the file before committing
```

Never edit a revision that has been applied anywhere; add a new one.

## Backup and restore

Take a backup **before every migration** and on a schedule.

```bash
# Docker stack: custom-format dump into ./backups (*.dump is git-ignored)
mkdir -p backups
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > backups/textile-$(date +%Y%m%d-%H%M%S).dump

# Restore into an EMPTY database
docker compose exec -T db sh -c 'createdb -U "$POSTGRES_USER" textile_restore'
docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d textile_restore --no-owner' < backups/textile-YYYYMMDD-HHMMSS.dump

# Without Docker
pg_dump -Fc "postgresql://textile:PASSWORD@localhost:5432/textile" > textile.dump
```

`backend/scripts/backup_db.sh` wraps the Docker backup. Keep the `UPLOAD_DIR` folder with the backups: it holds
the original report files, so any import can be re-run from them.

## Logins

Development (`ENVIRONMENT` not `production`) seeds one login, `admin`, with the shared demo password. A
production database starts with no users; create them:

```bash
python -m app.db.create_user --username gm --full-name "GM name" --role ADMIN   # prompts for the password (10+ characters)
```

## Tests

The PostgreSQL tests need a **dedicated** database whose name ends in `_test`; the suite drops and recreates its
`public` schema and never reads `DATABASE_URL`.

```bash
createdb textile_test
cd backend
TEST_DATABASE_URL="postgresql+psycopg://USER:PASSWORD@localhost:5432/textile_test" python -m pytest
```

Without `TEST_DATABASE_URL` those tests are reported as skipped.

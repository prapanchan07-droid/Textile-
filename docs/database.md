# Database: PostgreSQL, migrations, backup and restore

The application's target database is **PostgreSQL 16**. The weaving analytics need it (they use PostgreSQL
functions and time-zone-aware timestamps). SQLite is still read by one tool only: the one-time copy of the
old `ai_factory_manager.db` into PostgreSQL (see "Moving the old SQLite data").

## Configuration

Settings come from environment variables (or `backend/.env`, which is git-ignored). Set **either**:

| Variable | Meaning |
|---|---|
| `DATABASE_URL` | Full URL, e.g. `postgresql+psycopg://textile:PASSWORD@localhost:5432/textile` |
| `POSTGRES_HOST` / `POSTGRES_PORT` / `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | Pieces; the app builds the URL and escapes the password. `POSTGRES_PASSWORD` is required. |

Other relevant settings: `AUTO_MIGRATE` (run migrations at API start-up; `true` for local development, `false` in
Docker where the entrypoint runs them), `MILL_TIMEZONE` (default `Asia/Kolkata`; decides where a production day
begins), `ENVIRONMENT` (`production` hides the demo logins and makes the demo-data command refuse to run).

The app refuses to start if no database is configured, instead of silently creating an empty SQLite file.
No credentials are stored in the repository. `.env.example` files show the names only.

## Docker Compose

```bash
cp .env.example .env          # then set POSTGRES_PASSWORD and SECRET_KEY (openssl rand -base64 24 / -hex 32)
docker compose up -d --build
```

* `db` is `postgres:16-alpine` with the named volume `postgres_data` (survives `docker compose down`) and a
  `pg_isready` health check. The backend waits for it to be healthy. The database port is **not** published to the host.
* The backend entrypoint runs `alembic upgrade head` before starting the API.
* `docker compose config` fails with a clear message if `POSTGRES_PASSWORD` or `SECRET_KEY` is missing.
* `docker compose down -v` deletes the volumes, and with them the database. Do not use it on real data.

## Migrations (Alembic)

Version-controlled in `backend/alembic/versions/`:

| Revision | What it does | Reversible? |
|---|---|---|
| `0001` baseline | Adopts the tables the app already had (users, reports, imported records...). Each step is **skipped if the table already exists**, so a database made by the old start-up code is adopted without touching a row. | `downgrade` is a deliberate no-op: it never drops real data. |
| `0002` weaving schema | Adds the 18 `wv_*` tables. Nothing existing is altered. | Yes. `downgrade 0001` drops **only** the `wv_*` tables (and therefore all weaving data). Back up first. |

```bash
cd backend
alembic upgrade head          # apply
alembic current               # where the database is
alembic downgrade 0001        # undo the weaving schema (destroys weaving data: back up first)
alembic check                 # fail if the models and migrations disagree
alembic revision --autogenerate -m "describe the change"   # then review the file before committing
```

Never edit a revision that has been applied anywhere. Add a new one.

## Backup and restore

Use PostgreSQL's own tools. Take a backup **before every migration** and on a schedule.

```bash
# Docker stack: custom-format dump into ./backups (the file is not committed; *.dump is ignored)
mkdir -p backups
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > backups/textile-$(date +%Y%m%d-%H%M%S).dump

# Restore into an EMPTY database (create it first). --clean is intentionally not used.
docker compose exec -T db sh -c 'createdb -U "$POSTGRES_USER" textile_restore'
docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d textile_restore --no-owner' < backups/textile-YYYYMMDD-HHMMSS.dump
# check the restored copy, then switch POSTGRES_DB to it (or rename databases) once you are satisfied

# Without Docker (strip the "+psycopg" from the URL for the PostgreSQL tools)
pg_dump -Fc "postgresql://textile:PASSWORD@localhost:5432/textile" > textile.dump
```

`backend/scripts/backup_db.sh` wraps the Docker backup command. Test a restore regularly: a backup you have
never restored is not yet a backup.

## Moving the old SQLite data into PostgreSQL

Changing `DATABASE_URL` does **not** move data. The old database holds the users (with password hashes and
roles) and every imported report record. Move it with the explicit tool:

```bash
cd backend
# 1. Rehearse: copies, validates, then rolls back. Writes nothing to PostgreSQL.
python -m app.db.sqlite_to_postgres --source ai_factory_manager.db --target "$DATABASE_URL" --dry-run

# 2. Do it.
python -m app.db.sqlite_to_postgres --source ai_factory_manager.db --target "$DATABASE_URL"
```

For the Docker stack the SQLite file is on the `factory_data` volume at `/app/data/ai_factory_manager.db`:

```bash
docker compose run --rm backend sh -c 'python -m app.db.sqlite_to_postgres --source /app/data/ai_factory_manager.db --target "postgresql+psycopg://$POSTGRES_USER:$POSTGRES_PASSWORD@db:5432/$POSTGRES_DB" --backup-dir /app/data/backups'
```

What it guarantees:

* The source file is only read. A verified backup copy (SQLite online-backup API + integrity check + SHA-256) is written first.
* The target is migrated to the latest revision, then rows are copied with `INSERT ... ON CONFLICT DO NOTHING`.
  Nothing already in PostgreSQL is overwritten, updated, deleted or truncated.
* Everything is one transaction. Before it commits, every source primary key must exist in PostgreSQL and every
  user's id, username, role, active flag and **password hash** must match. Any mismatch rolls the whole copy back
  and the tool exits non-zero.
* Repeatable: a second run reports `0` inserted rows.

Per-table counts (source, inserted, already there) are printed. Keep `ai_factory_manager.db` and the backup until
you have signed in as each role and checked the data.

## First sign-in on a fresh production database

With `ENVIRONMENT=production` the demo logins are never created, so a brand-new database has no users. Create the
first one (it asks for the password, or reads it from an environment variable; it never takes it on the command line):

```bash
docker compose exec backend python -m app.db.create_user --username owner --full-name "Your Name" --role OWNER
# roles: OWNER, WEAVING_MANAGER, SHIFT_SUPERVISOR, MAINTENANCE, QUALITY  (passwords: at least 10 characters)
```

An existing username is refused; `--reset-password` changes only the password of that user. A database copied from
the old SQLite file keeps its existing users and does not need this.

## Weaving data

Reference data (shifts, stop reasons, defect types) is configuration: it is loaded automatically, only where
missing, and never overwrites what a mill has edited. Factory records are never created automatically.

```bash
cd backend
python -m app.weaving.seed reference          # shifts, stop reasons, defect types (safe anywhere)
python -m app.weaving.seed demo --days 21     # DEMONSTRATION data for development: refuses when ENVIRONMENT=production
python -m app.weaving.seed demo --reset-demo  # first delete ONLY rows marked DEMO, then reload (use after a schema change to the demo data)
```

The demo data is deterministic and idempotent (see the module docstring in `app/weaving/seed/demo.py`), every row
is marked `data_origin = 'DEMO'`, and the app labels any view that includes it. It adds only; it never deletes or
rewrites existing rows (the single exception: closing demo stoppages that were still open once their deterministic
end time has passed). To remove it, restore from a backup taken before seeding, or delete rows where
`data_origin = 'DEMO'` after reviewing them. A live mill loads its own records into the same tables (later phase:
file import and machine feeds) with `data_origin` `IMPORTED` or `LIVE`.

## Tests

The PostgreSQL tests need a **dedicated** database. The suite drops and recreates its `public` schema, so it only
runs against a database whose name ends in `_test`, and it never reads `DATABASE_URL`.

```bash
createdb textile_test
cd backend
TEST_DATABASE_URL="postgresql+psycopg://USER:PASSWORD@localhost:5432/textile_test" python -m pytest
```

Without `TEST_DATABASE_URL` the PostgreSQL tests are reported as **skipped** (not passed) and only the pure-logic
tests run.

## Rollback summary

| Situation | Action |
|---|---|
| Bad weaving migration | `alembic downgrade 0001` (loses weaving rows; restore from backup if you need them) |
| SQLite copy did not validate | Nothing to undo: it rolled back. Fix the cause and re-run. |
| Need the old SQLite stack back | The SQLite file and its backup were never modified: point `DATABASE_URL` at it (legacy modules only; weaving analytics need PostgreSQL) |
| Corrupt or wrong data in PostgreSQL | Restore the last good dump into a fresh database as shown above |

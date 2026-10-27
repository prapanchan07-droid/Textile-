# Weaving Operations Platform — Ashok Textiles

Decision support for the weaving GM and the mill owner. It imports the mill's own reports (daily TY/TS/SZ
production workbook, Tsudakoma and Toyota monitoring exports) and turns them into a command centre, loom
pages, fair machine comparisons, loss findings, alerts and incidents, group work allocation, maintenance work
orders and a GM-to-owner report. Imported data is always shown as historical, never as a live machine feed.

* What it does and how: [docs/weaving-platform.md](docs/weaving-platform.md)
* What each source file contains, how it maps, and its reconciliation results: [docs/data-sources.md](docs/data-sources.md)
* Database, migrations, backup and restore: [docs/database.md](docs/database.md)

## Quick start

Prerequisites: Python 3.10+, Node 18+, PostgreSQL 16+.

```bash
# backend
cd backend
python -m venv .venv && .venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env                                   # set POSTGRES_PASSWORD (or DATABASE_URL) and SECRET_KEY
python -m uvicorn app.main:app --reload --port 8000    # applies migrations when AUTO_MIGRATE=true

# frontend (new terminal)
cd frontend
npm install
npm run dev                                            # http://localhost:5173
```

Sign in with the development login `admin` / `Ashok@2026` (seeded only when `ENVIRONMENT` is not `production`;
create real logins with `python -m app.db.create_user --username NAME --role ADMIN`). Then open **Data imports**
and upload the reports, or from the command line:

```bash
cd backend
python -m app.mill.cli import "path/TY,TS,SZ-Production Report- Sepember - 2026.xlsx" path/13-10-2026-PICK.xls path/13-10-2026-MTR.xls path/11-10-2026-ty.xls
python -m app.mill.cli bootstrap-groups          # the 11 groups (empty; name them and assign looms on the Groups page)
```

API docs: http://localhost:8000/api/v1/docs · Health: http://localhost:8000/api/v1/health

## Docker

```bash
cp .env.example .env     # set POSTGRES_PASSWORD and SECRET_KEY first
docker compose up -d --build
```

UI on http://localhost:5173 (nginx serves the UI and proxies `/api/`), API on :8000. PostgreSQL data lives in
the `postgres_data` volume and uploaded originals in `factory_reports`; `docker compose down -v` deletes them.

## Tests and build

```bash
cd backend
TEST_DATABASE_URL="postgresql+psycopg://USER:PASSWORD@localhost:5432/textile_test" python -m pytest   # database name must end in _test
cd ../frontend && npm run build
```

Without `TEST_DATABASE_URL` the PostgreSQL tests are skipped; the parser and formula tests still run.
`MILL_SAMPLE_DIR=<folder with the real files>` additionally imports the mill's actual files and checks them.

## Repository

```
backend/
  app/mill/            domain: models, importers, analytics, alerts, telemetry, reports, CLI, background jobs
  app/api/v1/mill/     REST API (/api/v1/mill/...)
  app/core, app/db     config, auth, sessions, migrations runner, logins
  alembic/versions/    0001 = the whole schema
  tests/               parsers (grids.py mirrors the real layouts), platform tests on PostgreSQL
frontend/src/
  features/            one folder per page (command, looms, production, compare, alerts, tasks, groups, ...)
  design/              design system, tables, charts
  api/mill.ts          React Query hooks; types/mill.ts payload shapes
docs/                  weaving-platform.md, data-sources.md, database.md
```

`uploaded_reports/` (originals, may contain operator names), `.env`, databases and dumps are git-ignored.

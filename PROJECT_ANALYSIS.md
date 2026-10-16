# Textile- Project Analysis

Read-only analysis of the repository at `/mnt/c/Users/Admin/Documents/gokul/Textile-` (branch `main`, last commit `73e4d00`). No existing file was modified; this document is the only addition.

## 1. What the project is

**AI Factory Manager – Ashok Textiles**: a decision-support platform for a textile mill. It began as a report-ingestion and dashboard tool for the whole factory (spinning to weaving) and has become a **weaving decision-intelligence platform** with role-specific pages. Its stated aim is not to be an ERP. The flow it implements is: data → analytics → problem detection → evidence-backed findings → recommendations → human-approved actions.

Design rules visible in the code and docs (`docs/weaving-intelligence.md`):
- Metrics and "AI" features are deterministic statistics or optimisation. No LLM is involved.
- Facts, statistical signals, hypotheses and verified causes are kept separate. A verified cause stays empty until a person records it.
- Nothing consequential happens without approval. The scheduler records a plan and raises actions, and moves no loom.

## 2. Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite 5, Tailwind 3, React Router 6, TanStack Query 5, Axios, Recharts, lucide-react |
| Backend | FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, psycopg 3, PyJWT, pandas, openpyxl/xlrd, pypdf, Pillow |
| Database | PostgreSQL 16 (required by the weaving analytics). SQLite remains only as a legacy source for a one-time copy. |
| Deploy | Docker Compose (`db` + `backend` + `frontend`/nginx). Netlify and Vercel SPA configs exist for the frontend. |
| Tests | pytest. The PostgreSQL tests run only when `TEST_DATABASE_URL` is set. |

## 3. Repository layout

```
Textile-/
├── backend/
│   ├── app/
│   │   ├── main.py                FastAPI app, CORS, exception handlers, lifespan (init_db)
│   │   ├── api/deps.py            JWT bearer auth, require_roles / require_section
│   │   ├── api/v1/                auth, weaving, health + legacy routers (see §5)
│   │   ├── core/                  config, roles (ROLE_SECTIONS), security, logging, exceptions
│   │   ├── db/                    session, init_db, Alembic runner, seed_users, sqlite_to_postgres
│   │   ├── models/                User, ingestion records, system info, template_data
│   │   ├── weaving/
│   │   │   ├── models.py          18 wv_* tables
│   │   │   ├── analytics/         calc, facts, stats, calendar, sensors, orders, forecast,
│   │   │   │                      scheduler, compare, workforce, investigations, definitions
│   │   │   ├── pages/             One payload builder per sidebar page (overview, ops, machines, people, commercial, intel)
│   │   │   └── seed/              Deterministic demo data (python -m app.weaving.seed demo)
│   │   ├── services/              Legacy module services + ingestion/ and template/
│   │   └── schemas/               Pydantic schemas
│   ├── alembic/versions/          0001 baseline, 0002 weaving schema, 0003 machine details/sensors/employees
│   ├── tests/                     9 test modules
│   ├── Dockerfile, docker-entrypoint.sh, scripts/backup_db.sh
├── frontend/
│   └── src/
│       ├── app/                   router.tsx, state.ts
│       ├── auth/                  AuthContext, LoginPage, guards, token
│       ├── layout/                AppShell, Sidebar, CommandPalette, nav.ts (role-built menu)
│       ├── design/                UI kit, charts, viz (Heatmap, Sparkline, StatTile)
│       ├── features/weaving/      15 role pages (the live product)
│       ├── features/{data,admin}  Data Imports, System Status (live)
│       ├── features/{production,quality,workforce,assets,actions,commercial,control-tower}  Legacy pages (see §7)
│       ├── api/ lib/ types/       Query hooks, formatters, backend types (pages.ts is the weaving contract)
├── docs/                          database.md, weaving-intelligence.md, REDESIGN.md
├── docker-compose.yml, .env.example
├── README.md, WHAT_WE_BUILT.md
└── sample_synthetic_data.xlsx
```

About 25k lines of Python, TypeScript and Markdown are tracked, excluding lockfiles.

## 4. Roles and access control

Five roles, defined in `backend/app/core/roles.py`. `ROLE_SECTIONS` is the single table that drives both the frontend menu (through `GET /auth/me`) and API authorization (`require_section`), so the two cannot drift apart.

| Role | Landing page | Other pages |
|---|---|---|
| Owner / MD | owner | orders, scheduler, insights, compare, actions |
| Weaving Manager | command | production, stoppages, machines, workforce, orders, scheduler, insights, compare, actions |
| Shift Supervisor | cockpit | handover, stoppages, machines, workforce, actions |
| Maintenance | maintenance | machines, stoppages, actions |
| Quality | quality | insights, compare, actions |

Only Owner and Weaving Manager (the "financial roles") see rupee figures and can approve plans. Only they can use Data Imports and System Status, and the whole legacy API (ingestion, overview, production, machines, manpower_quality, revenue_loss, decision_center, machine_comparison) is restricted to them in `router.py`.

Auth is JWT (HS256, 480-minute expiry). Login returns the same error for an unknown user and a wrong password.

## 5. Backend API surface

- **Public**: `/health`, `/auth/login`, `/auth/demo-accounts`. The demo-accounts route is documented as hidden when `ENVIRONMENT=production`.
- **Weaving** (`api/v1/weaving.py`, 415 lines):
  - 15 `GET /weaving/pages/{page}` payloads, plus `/pages/machines/{loom}`.
  - Analytics: `/analytics/{definitions,production,stoppages,quality}` with a `group_by` parameter.
  - Event lists: `/events/stops` and `/inspections`, both paginated.
  - Investigation endpoints: `/investigations/findings`, `/priorities` and `/style/{code}/beam-change`.
  - Compare: `/compare/options` and `/compare/run`.
  - Writes: `POST /actions`, `/actions/{ref}/approve`, `/notes`, `/notes/{id}/resolve` and `/scheduler/decision`.
- **Legacy** (owner/manager only): ingestion upload-job and polling, plus overview, production (and lineage), machines, manpower-quality, revenue-loss, decision-center and machine-comparison.

## 6. Weaving intelligence

The analytics live in `backend/app/weaving/analytics/`.

- **Data model**: `wv_*` tables for looms, styles, yarn lots, beams, orders, operators, shift assignments and attendance. Facts cover loom readings (hourly, including vibration, motor temperature, air pressure and power), stop events, inspections and defects, maintenance events, notes, schedule plans and actions. Business keys are unique, which keeps import and seed idempotent. `data_origin` marks DEMO, IMPORTED or LIVE.
- **Machine abnormality watch** (`sensors.py`): each loom is compared with its own normal, giving critical, warning or watch alerts.
- **Health score**: 0–100, with each deduction shown separately.
- **Findings** (`investigations.py`, the largest module at 576 lines): loom decline, repeated stoppages, warp breaks by beam or yarn lot, shift defect outliers and maintenance priorities.
- **Delivery-risk forecast** (`orders.py`) and **output forecast** (`forecast.py`): the forecast picks smoothing on a hold-out and prints its error. No forecast is made with less than about 10 days of history.
- **AI Scheduler** (`scheduler.py`): 28-day simulation, as booked versus proposed, using lookahead hill-climbing with a style-change cost. It respects loom-type and reed-space constraints and avoids low-health looms for priority-A orders. It needs owner or manager approval.
- **Compare** (`compare.py`): up to 8 entities side by side. A difference is flagged only when it is statistically unlikely to be chance *and* large enough to matter.
- **Workforce signal**: loom-adjusted, so a faulty loom is not blamed on its weaver.

Strength: the documentation states what each feature does *not* claim, which is unusual and good.

## 7. Frontend

- Routes are in `app/router.tsx`: `/login`, then `RequireAuth`, then `AppShell`, then 15 `/weaving/*` pages guarded by `RequireSection`, plus `/data` and `/admin/system`. A per-route `errorElement` keeps a crashing page from taking down navigation.
- The menu is built per role by `layout/nav.ts` from `sectionsFor(user)`, with a "Platform" group for the owner and manager.
- There is a command palette and a shared design system (`design/`).
- `types/pages.ts` mirrors the backend page payloads. `backend/tests/test_page_contract.py` parses it and checks both directions against live API output.

## 8. Data ingestion (legacy but still active)

- `services/ingestion/` (extractor, normalizer, ingestion_service) handles XLSX, XLS, CSV, PDF and images, with SHA256 duplicate protection and background jobs.
- `services/template/` builds a downloadable Excel template (one sheet per data set) and imports filled templates. Pages switch from built-in synthetic data to uploaded data once data for them exists.
- Reports are staged in `backend/uploaded_reports/` (git-ignored; may hold employee data).

## 9. Deployment and operations

- `docker-compose.yml`: Postgres 16 with a health check, backend (migrations run in the entrypoint, then it drops to uid 10001), and frontend served by nginx on port 5173 and proxying `/api/`. The database port is not published. Compose refuses to start without `POSTGRES_PASSWORD` and `SECRET_KEY`.
- `AUTO_MIGRATE=true` runs migrations at API start in development. Otherwise `init_db` fails fast if the schema is not at head.
- `docs/database.md` covers backup, restore, migration and the SQLite-to-Postgres copy.
- Demo mode: `python -m app.weaving.seed demo` refuses to run when `ENVIRONMENT=production`. Demo logins are seeded only outside production.

## 10. Issues and risks found

Ordered roughly by importance.

1. **Weak secrets in the local root `.env`.** It contains `POSTGRES_PASSWORD=admin` and `SECRET_KEY=ashoktextiles`. The file is correctly git-ignored, and `.env.example` itself holds only placeholders, but `ENVIRONMENT=production` is set alongside these values. A short, guessable `SECRET_KEY` lets anyone forge login tokens, so it should be replaced with `openssl rand -hex 32` before real use.
2. **Code defaults that are unsafe if env is missing.** `config.py` falls back to `SECRET_KEY="ashok_textiles_dev_secret_key_change_in_production"`. There is also a hardcoded LAN IP in the default `CORS_ORIGINS`. Consider failing at start-up when `ENVIRONMENT=production` and the key is the default.
3. **Large block of orphaned legacy frontend code.** `features/{production,quality,workforce,assets,actions,commercial,control-tower}` are not imported by the router and nothing outside them references them, except each other and `layout/AppShell.tsx` using `api/queries.ts`. The matching legacy types (`overview.ts`, `machines.ts` and others) and the `api/queries.ts` hooks serve those pages. This is dead weight and invites confusion, since `weaving/production` and `weaving/quality` have the same names.
4. **Stale and contradictory documentation.**
   - `README.md` feature 5 says the weaving module runs on mock data in `services/weaving_service.py`. That file no longer exists; weaving is now database-backed.
   - `WHAT_WE_BUILT.md` still describes a SQLite-based architecture and an "ERP" positioning, which conflicts with the Postgres move and the "not an ERP" vision.
   - `health.py` reports `active_module="MODULE_01 - Project Foundation"`.
   - The `docker-compose.yml` comment about `docker-compose.override.yml` refers to a file that does not exist (harmless).
5. **Unrelated root `package.json`.** An untracked `package.json` at the repo root lists `@supabase/ssr` and `@supabase/supabase-js`, with a `node_modules/` and lockfile beside it. Nothing in the code uses Supabase. It looks accidental (the folder is git-ignored for `node_modules`, but `package.json` and its lockfile are untracked and would be committed by `git add .`).
6. **Working tree is heavily dirty** (about 100 modified files on `main`), apparently line-ending or formatting churn from the WSL/Windows mix, since the files are on a `/mnt/c` mount. Check with `git diff --stat` and `git diff -w --stat` before committing, and consider a `.gitattributes` with `* text=auto eol=lf`. The shell script `docker-entrypoint.sh` already needs a `sed -i 's/\r$//'` workaround in the Dockerfile, which supports this theory.
7. **Binary and data files in the tree.** `backend/uploaded_reports/<uuid>_sample_synthetic_data.xlsx` is tracked (the ignore rule allows only `.gitkeep`, so it was added before the rule). `backend/ai_factory_manager.db` and `backend/backups/*.bak.db` are present on disk but ignored. Confirm they hold no real data before sharing the repo.
8. **Test coverage is gated.** All PostgreSQL tests are skipped without `TEST_DATABASE_URL`, so a plain `pytest` run proves little. There are no frontend tests, and no CI configuration in the repo.
9. **Security details worth a review.**
   - There is no login rate limiting or lockout.
   - Tokens are stateless with an 8-hour life and no revocation.
   - `datetime.utcnow()` is used (deprecated in newer Python).
   - Debug-mode CORS allows any private-range or Tailscale host on port 5173 (only when `DEBUG` is true).
   - The frontend stores the token client-side (`auth/token.ts`), which should be checked for XSS exposure.
10. **Only synthetic data exists.** Per the project's own notes, the machine-watch signals and forecasts have not been validated on real history. The next real milestone is a real-data import or machine feed.
11. **Docker image builds are unverified** on this machine (registry access problems from SSH, per project notes).

## 11. Suggested next steps

1. Rotate the secrets, and make production start-up refuse default keys.
2. Delete or archive the orphaned legacy frontend pages and unused types and hooks (after confirming `AppShell` only needs a small part of `api/queries.ts`).
3. Update `README.md`, `WHAT_WE_BUILT.md` and the health endpoint text to match the current architecture.
4. Remove the stray root `package.json`, `package-lock.json` and `node_modules`.
5. Normalise line endings with `.gitattributes`, then review the real diff before committing.
6. Add CI that runs `pytest` against a Postgres service and `npm run build`.
7. Plan the real-data path (importer or machine feed) and validate the sensor and forecast features against real breakdown history.

## 12. How to run (summary)

```bash
# Docker
cp .env.example .env   # set strong POSTGRES_PASSWORD and SECRET_KEY
docker compose up -d --build        # UI http://localhost:5173, API docs http://localhost:8000/api/v1/docs

# Local development
cd backend && pip install -r requirements-dev.txt && cp .env.example .env   # set POSTGRES_PASSWORD
python -m uvicorn app.main:app --reload --port 8000
python -m app.weaving.seed demo --days 21        # demo data (never in production)
cd frontend && npm install && npm run dev        # http://localhost:5173

# Tests (needs a dedicated Postgres database whose name ends in _test)
cd backend && TEST_DATABASE_URL="postgresql+psycopg://USER:PASS@localhost:5432/textile_test" python -m pytest
```

Demo logins (non-production only): `owner`, `manager`, `supervisor`, `maintenance`, `quality`, as listed by the project notes.

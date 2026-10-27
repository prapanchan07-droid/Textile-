# Weaving operations platform

Decision support for the GM and the owner: imported production reports become one database of loom-shift
records; the pages, alerts, tasks and owner reports all read from it. This page describes what exists, how it
works and what is still needed from the mill and the machine vendors.

## Architecture

```
 .xls / .xlsx / .csv upload ──► importers (detect by structure, parse, validate, reconcile)
                                   │  original file kept unchanged (UPLOAD_DIR), raw rows kept (raw_source_rows)
                                   ▼
                    shift_production (one row per loom, date, shift, source)
                                   │
   machine adapters ──► telemetry_samples (LIVE / SIMULATED)          people enter: groups, tasks,
   (simulator; Toyota/Tsudakoma                                        work orders, targets, reports
    awaiting vendor interface)                                                 │
                                   ▼                                           ▼
              analytics/metrics.py (one definition per KPI) ──► pages, findings, alert engine, owner report
```

* Backend: FastAPI + SQLAlchemy 2 + PostgreSQL + Alembic (`backend/app/mill`, API under `/api/v1/mill`).
* Frontend: React + React Query + Tailwind, reusing the existing shell and design system (`frontend/src/design`).
* Background: an in-process loop (`app/mill/jobs.py`) polls enabled machine connections and checks deadlines,
  stale data and escalation every `BACKGROUND_INTERVAL_SECONDS` (60). Imports commit in a background task and the
  page polls their status. Alert rules run after every import commit.

## Pages

| Page | Route | What it answers |
|---|---|---|
| Command centre | `/` | Period KPIs (meters, time-weighted efficiency, kilopicks, warp/weft per 100k picks, looms reporting, alerts, tasks), efficiency and meters by day per category, category and shift tables, loss findings with evidence, group status, alerts needing attention. Filters: period, category, shift, source, group. |
| Loom floor | `/looms` | Every loom as a tile (efficiency, standing vs peers, trend, latest record, alerts, work orders, live state) or a sortable table. |
| Loom detail | `/looms/:id` | Configuration, KPIs, daily trend vs peer median, shift comparison, peer table, per-sensor stops (Tsudakoma), findings, statistical anomalies, recommendations, alerts, tasks, work orders, group history, every shift record with its import batch. |
| Production & shifts | `/production` | Day × shift meters, efficiency heatmap, category × shift, style mix. |
| Compare machines | `/compare` | Looms, shifts, styles, widths, categories, groups or days side by side; looms ranked against their peer group. |
| Air & energy | `/energy` | Measured air / energy only; states what is missing (currently everything) and shows no estimate. |
| Alerts | `/alerts` | Active / unacknowledged / resolved alerts, evidence, history, acknowledge, assign, comment, resolve (note required), reopen, create task or work order; rules and notification channels. |
| Tasks | `/tasks` | GM task list with status workflow, comments, completion notes, escalation to the owner. |
| Groups | `/groups` | Daily board per group (open, blocked, overdue, completed in 24 h, alerts), group setup, dated loom and people assignments, people list. |
| Maintenance | `/maintenance` | Work orders (breakdown, preventive with planned date, inspection, adjustment), downtime and confirmed cause entered by maintenance. |
| Owner reports | `/reports`, `/reports/:id` | Draft from a period (and optional shift), 13 sections, GM commentary, publish (freezes numbers), owner acknowledgement and comment, Excel export, print to PDF. |
| Data imports | `/imports` | Upload, preview (plan, completeness, reconciliation, row-level issues), commit or discard, history. |
| Connectivity | `/connectivity` | Per-loom adapter, host, poll interval, credentials variable name, state, last reading and error. |
| Targets & audit | `/settings` | Production targets, metric definitions, audit log. |

## Metric rules (see `app/mill/analytics/metrics.py` and the "Metric definitions" tab)

* **Efficiency** is time-weighted: Σ(eff × minutes) / Σ minutes, minutes = run + stop when the source gives them
  (Toyota export) else the 480-minute shift. Never summed, never averaged across unequal periods.
* **Stop rates** are per 100,000 picks: Σ stops / Σ kilopicks × 100, over records having both values.
* **Missing values** are excluded from sums and counted in `coverage`; a missing value never becomes 0.
* **One source per loom-shift**: the mill report wins over a machine export by default; every number carries
  its source and the source filter shows either alone. Stop rates and meters should be compared within one source
  (TY 340 cm looms: the mill report counts both panels).
* **Peers** = same category, reed width, dominant style and source; comparisons need 3 or more looms.
* **Modeled** numbers (meters gap vs peers) are labelled as estimates with their assumption and never shown as
  realised loss or profit. No rupee figure is computed: no prices, costs or tariffs exist in the data.

## Alerts and notifications (`app/mill/alerts`)

Default rules (editable on the Alerts → Rules tab):

| Code | Condition | In a row | Severity |
|---|---|---|---|
| EFF_LOW | efficiency < 80% | 2 | Warning |
| EFF_CRITICAL | efficiency < 60% | 1 | Critical |
| EFF_DROP_BASELINE | efficiency more than 8 pts under the loom's 14-day median (same source) | 2 | Warning |
| EFF_ANOMALY | robust z-score < −3.5 vs the loom's previous 14 days | 1 | Info |
| WARP_STOP_RATE / WEFT_STOP_RATE | > 6 / > 15 per 100k picks (TY, TS only) | 2 | Warning |
| RPM_SHIFT | RPM differs from the 14-day median by > 50 | 1 | Info |
| METERS_BELOW_TARGET | > 10% under the meters-per-shift target (only where configured) | 2 | Warning |
| NO_RECORD | loom with records in the last 30 days but none on its category's latest day | 1 | Warning |
| AIR_PER_METER | air Nm3/m above a limit (disabled until measured air exists) | 1 | Warning |
| TELEMETRY_STALE | enabled connection without a reading within `TELEMETRY_STALE_SECONDS` | 1 | Warning |
| TASK_OVERDUE | open HIGH/CRITICAL task past due | 1 | Warning |
| PM_OVERDUE | preventive work order past its planned date | 1 | Warning |

Lifecycle: one alert per rule and loom (`dedup_key`); a newer breaching shift refreshes it (occurrences,
values) instead of creating another; when the condition stops it is marked "condition cleared" but stays open
until a person resolves it with a note; a resolved alert re-opens only for a shift newer than the one handled
and after the cooldown, so historical data never re-triggers it. Unacknowledged alerts escalate once per
`escalate_after_hours` interval and notify again. Every step is an `alert_events` row and an audit entry.

Channels: **in-app only** (the bell; DELIVERED). Email, SMS and WhatsApp are listed as NOT_CONFIGURED; adding
one needs a provider account, credentials in the environment and a delivery test, then an implementation in
`alerts/notify.py`. A delivery failure is logged on the notification and never stops evaluation.

## Machine connectivity (`app/mill/telemetry`)

* Common adapter interface, read-only (no method can write to a loom). Each adapter handles its configuration,
  credentials (by environment-variable name), timeouts, field mapping and errors; the collector handles polling
  intervals, exponential back-off (capped at 30 min), timestamp validation (future or stale readings rejected),
  connection health, and retention (`TELEMETRY_RETENTION_DAYS`).
* **Simulator**: deterministic readings stored as `SIMULATED` and shown with a "Simulated" badge everywhere.
* **Toyota (TOYOTA_TMS) and Tsudakoma (TSUDAKOMA_TISS)**: not implemented on purpose. They report
  `AWAITING_VENDOR_INFO`. No endpoint, port, protocol or register map is assumed.
* States shown: NOT_CONFIGURED, AWAITING_VENDOR_INFO, CONFIGURED (not polling), CONNECTED (fresh reading),
  STALE (older than the window), OFFLINE / ERROR. A connection that never delivered is never shown as healthy.

Recommended network design (NIST SP 800-82r3, NCSC OT secure-connectivity principle 4):

```
 Looms ── OEM monitoring server / approved edge gateway  (OT network, unchanged)
                     │  one-way or tightly firewalled, authenticated, read-only
               collector host (DMZ)  ── outbound only ──► application (IT network)
```

Never expose looms or the monitoring server to the internet; no network scanning or credential guessing; one
service account per integration with the least privilege the vendor supports.

## GM-to-owner workflow

1. GM creates a draft for a day (or range, or one shift): the numbers are computed from stored data.
2. GM refreshes it after late imports, writes the commentary (required), decisions needed and risks, then
   publishes. Publication freezes the snapshot: later imports never change it (tested).
3. The owner opens the report, acknowledges it and may leave a comment.
4. Excel export renders the stored snapshot; "Print / PDF" uses the browser's print (A4 friendly).

Sections: production overview; output vs target; efficiency by shift and category; deviations; stop problems;
critical alerts; maintenance; groups; tasks; energy and air; improvement opportunities (modeled); decisions
needed; risks. A "calculation basis" block lists the import batches and formulas behind the numbers.

## Roles

One role today: **ADMIN** (as requested; more roles later). Every `/api/v1/mill` route requires a signed-in user
with a permitted role, enforced in `app/api/v1/router.py`. To add Owner / GM / group leader / operator /
maintenance roles: add them to `app/core/roles.py`, narrow routers or routes with `require_roles(...)`, and for
group leaders filter queries by their group (`GroupMemberAssignment`); the UI menu is built in
`frontend/src/layout/nav.ts`.

## Running it

```bash
# backend (PostgreSQL required)
cd backend
cp .env.example .env            # set DATABASE_URL or POSTGRES_*; SECRET_KEY
alembic upgrade head            # or AUTO_MIGRATE=true (development)
python -m app.db.create_user --username gm --full-name "GM" --role ADMIN   # production logins
uvicorn app.main:app --reload   # API + background loop on :8000

# frontend
cd frontend && npm install && npm run dev   # :5173, proxies /api to :8000

# data
python -m app.mill.cli import FILE...       # or the Data imports page
python -m app.mill.cli bootstrap-groups     # 11 empty groups (or the button on the Groups page)
python -m app.mill.cli evaluate-alerts
python -m app.mill.cli collect-once         # one telemetry cycle (enabled connections only)

# tests
cd backend && TEST_DATABASE_URL=postgresql+psycopg://USER@HOST:5432/textile_test pytest
cd frontend && npm run build
```

Several API workers: keep `BACKGROUND_JOBS_ENABLED=true` on one only, or schedule `collect-once` and
`evaluate-alerts` externally.

## Needed from the mill and vendors

| Needed | For |
|---|---|
| Loom models / generations per loom; confirmation of the 340 cm "×2" panel counting; SZ RPM / pick semantics | Correct machine master data and cross-source comparisons |
| Names of the 11 groups, leaders, loom-to-group and people-to-group lists with dates | Group views, group targets, accountability |
| Shift targets (meters or efficiency per loom/category) | Production vs target and the target alert |
| Toyota: documented read interface of the monitoring system (or export automation), network path, service account | Live data for TY looms |
| Tsudakoma: documented interface of the monitoring system / TISS, network path, service account; enabling air consumption | Live data and air for TS looms |
| Sulzer: what monitoring exists at all; warp/weft stop counts in the daily report | Any SZ stop analysis |
| Air: per-loom flow meters or OEM air values; compressor specific power (kWh/Nm3) | Air per meter, compressed-air cost |
| Electricity: meters per loom / group feeder / shed, tariff (Rs/kWh) | kWh per meter, energy cost |
| Stop reasons and durations (operator entry or OEM stop log), maintenance history with failure outcomes | Root-cause analysis; any predictive-maintenance model |
| Fabric price / contribution per meter | Any rupee figure for losses or opportunities |
| Email/SMS/WhatsApp provider and credentials | External notifications |

## Backlog (by business impact and dependency)

1. **Roles** beyond ADMIN with group-scoped data for group leaders (code points listed above).
2. **Live connectivity** for TY and TS once the vendor interfaces are documented (adapter skeletons exist).
3. **Operator stop-reason capture** (tablet form per loom-shift) to turn stop counts into causes.
4. **Energy and air import** (meter readings CSV) feeding the Air & energy page and AIR_PER_METER rule.
5. **External notification channel** (email first) with delivery retries and per-user preferences.
6. **Scheduled owner report** (draft created automatically each morning, GM reviews and publishes).
7. **Predictive maintenance**: only after months of timestamped telemetry, stop logs and maintenance outcomes;
   evaluate precision, false alarms, missed events and lead time per machine type before any claim.
8. **AI-assisted Q&A** over the metric layer (tool-calling an LLM against these endpoints, citing period, metric
   definition and source for every number). Not built: no model provider is configured, and the deterministic
   pages already answer the listed questions.
9. Attendance / operator-per-loom import when the mill has it.

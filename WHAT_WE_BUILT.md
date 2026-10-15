# 🏭 Ashok Textiles — AI Factory Manager & ERP Platform
## Comprehensive Build Summary & System Documentation

> **Status**: Production-Ready / Active Redesign Architecture  
> **Target Scale**: Composite Textile Mill (Spinning to Weaving, 1,000+ Workers, ₹3,000 Cr Turnover)  
> **Last Updated**: October 2026

---

## 📌 Executive Summary

The **AI Factory Manager** is a purpose-built, real-data ingestion, operational intelligence, and decision-support platform engineered specifically for Ashok Textiles. The platform replaces fragmented paper records, uncoordinated shift spreadsheets, and manual supervisor logbooks with a centralized, data-driven operational system.

It bridges the gap between machine-floor telemetry, shift supervisors, lab technicians, and senior executive leadership (MD/CXO, Plant Heads, Finance, QA, Maintenance).

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                   FRONTEND (React 18 + Vite + TypeScript)              │
│  - AppShell Layout & Collapsible Navigation   - Global Command Palette  │
│  - Design Tokens (Light/Dark CSS HSL)         - React Query Cache       │
│  - Deep-linked URL State (Period/Date/Asset)  - Responsive Drawers      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ REST API (JSON / Multipart)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI + Pydantic v2)                   │
│  - Asynchronous Background Job Queue          - Strict Reconciliation  │
│  - Template Spec Engine & Sample Generator    - Data Lineage Tracer    │
│  - Comprehensive REST API Endpoints           - SQLite / SQLAlchemy    │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
                    ▼                                ▼
┌──────────────────────────────────────┐  ┌──────────────────────────────┐
│       INGESTION & PARSING ENGINE     │  │       STORAGE & DATABASE     │
│ - Multi-file Upload (XLSX, CSV, PDF) │  │ - SQLite (WAL Enabled)       │
│ - Department Auto-segmentation       │  │ - Reports & Raw Lineage      │
│ - OCR & Vision (PyPDF, Pillow)       │  │ - Production & Downtime Recs │
│ - SHA-256 Checksum De-duplication    │  │ - Machine Daily & Quality    │
└──────────────────────────────────────┘  └──────────────────────────────┘
```

---

## 🧩 What Has Been Built: Core Subsystems

### 1. Universal Data Ingestion & Job Pipeline
* **Multi-Format Processing**: Ingests multi-department factory logs in `XLSX`, `XLS`, `CSV`, `PDF`, and scanned reports via image extraction (`PyPDF`, `Pillow`).
* **Department-Aware Auto-Parsing**: Intelligently identifies and sections out data for:
  * `Blowroom`
  * `Carding`
  * `Draw Frame`
  * `Combing`
  * `Simplex (Speed Frame)`
  * `Ring Frame`
  * `Airjet Spinning`
  * `Vortex Spinning`
  * `Weaving`
* **Asynchronous Multi-File Job Queue**:
  * Concurrent file staging to `uploaded_reports/`.
  * Background job creation (`/api/v1/ingestion/upload-job`) returning a unique `job_id`.
  * Real-time progress polling (`/api/v1/ingestion/job/{job_id}`) providing percentage completion, processed count, and per-file validation badges.
* **Integrity & De-duplication**:
  * SHA-256 file checksum hashing prevents duplicate uploads.
  * Audit traceability linking every production record to `source_file`, `source_sheet`, `source_row`, and `source_column`.

---

### 2. Standardized Factory Data Template System
* **Two-Way Template Engine** (`backend/app/services/template/`):
  * **Blank Template Generator**: Generates an `.xlsx` workbook containing validated sheets:
    * `Machine_Data`: Machine ID, Unit, Section, Shift, Targets, Actuals, Downtime, Stoppages, Power Events, Energy, Maintenance.
    * `Manpower`: Department-level required vs deployed headcount, absenteeism, shift details.
    * `Quality`: Lab testing parameters (Ne count, CSP, U%, IPI, Hairiness) against tolerance limits.
    * `Business`: Daily revenue, orders, dispatches, collections, and outstanding receivables.
    * `Stock`: Current raw material/yarn inventory valuation vs safety headroom limits.
    * `Actions`: Open issues, assigned action items, owners, and resolution statuses.
    * `Instructions`: Explicit guidance on expected data types, valid values, and column schemas.
  * **Sample Data Generator**: Produces a fully populated 7-day realistic factory dataset for quick onboarding and demonstrations.
* **Granular Sheet Activation**:
  * Ingesting a template with only specific sheets (e.g., `Quality`) selectively updates only that domain in the UI without wiping baseline data for others.
  * Ingesting updated data for an existing date seamlessly updates records without creating orphan duplicates.

---

### 3. Backend API Services & Business Logic
The backend is structured into modular FastAPI routers (`backend/app/api/v1/`):

| Router Endpoint | Core Service | Functionality |
| :--- | :--- | :--- |
| `/api/v1/overview` | `overview_service.py` | Aggregates daily output, target achievement, shift-wise distribution, top production loss causes, priority machines, and executive analyst briefing. |
| `/api/v1/production` | `production_service.py` | Delivers department and shift reconciliation ($\sum Shift Actuals = Cumulative$), factor analysis, gap analysis, and lineage traceability. |
| `/api/v1/machines` | `machines_service.py` | Fleet register, planned vs unplanned downtime, stoppage counts, power event frequencies, and maintenance dates. |
| `/api/v1/machine-comparison`| `machine_comparison_service.py` | Multi-machine benchmarking, radar/attribute comparisons, and head-to-head showdowns (energy efficiency in kWh/kg, quality index). |
| `/api/v1/manpower-quality` | `manpower_quality_service.py` | Quality lab parameters vs specification thresholds, defect rates, warp/weft breaks, and departmental staffing gaps. |
| `/api/v1/revenue-loss` | `revenue_loss_service.py` | Financial performance, cash collections, sales order fulfillment, revenue trends, and inventory headroom. |
| `/api/v1/decision-center` | `decision_center_service.py` | Root-cause analysis, "Where & Why" evidence cards, impact projections, and action tracking items. |
| `/api/v1/ingestion/*` | `ingestion_service.py` | File upload handling, async job polling, template downloading, and raw report ingestion. |
| `/api/v1/health` | `health.py` | API uptime check, database status, table record counts, and data freshness metrics. |

---

### 4. Database Models & Persistence Layer
Relational schemas implemented using SQLAlchemy ORM (`backend/app/models/`):

* **Report Records (`reports`)**: Tracks all ingested files, file hashes, timestamps, extraction confidence scores, and status flags.
* **Production Records (`production_records`)**: Shift, department, unit, machine type, target kg, actual kg, gap kg, achievement %, and precise source file row/column coordinates.
* **Downtime Records (`downtime_records`)**: Machine ID, downtime duration (minutes), production loss kg, reason categories, and remarks.
* **Quality Records (`quality_records`)**: Yarn count, quality score, defect rates, warp breaks, and weft breaks.
* **Energy Records (`energy_records`)**: Shift-level kWh consumed, energy per kg (UKG).
* **Manpower Records (`manpower_records`)**: Shift & department allocated workers, present count, and attendance gaps.
* **Machine Daily Records (`machine_daily_records`)**: Machine-level daily logs with stoppage counts, power trips, energy, quality ratings, and maintenance schedules.
* **Quality Parameter Records (`quality_parameter_records`)**: Specific lab test results mapped against upper/lower specification limits.
* **Business Daily Records (`business_daily_records`)**: Daily revenue, order intake, dispatch meterage, collections, and pending dues.
* **Stock Records (`stock_records`)**: Departmental stock valuations vs capacity limits.
* **Action Item Records (`action_item_records`)**: Operational action tracker items with issue description, action plan, owner, and status (`OPEN`, `IN_PROGRESS`, `COMPLETED`).

---

### 5. Frontend Architecture & Design System
* **Modern Stack**: React 18, TypeScript, Vite, Tailwind CSS, TanStack React Query v5, Lucide React icons, and React Router v6.
* **Design Token Engine** (`src/index.css`):
  * Semantic HSL color variables (`--bg`, `--card`, `--border`, `--text`, `--accent`, etc.).
  * Native Light and Dark theme support with automatic system detection or manual user toggle.
  * Contrast-validated, color-blind friendly palettes for status indicators and charts.
* **Indian Financial & Metric Formatting** (`src/lib/format.ts`):
  * Currency values formatted automatically into ₹ Lakhs (`₹ L`) or ₹ Crores (`₹ Cr`) with Indian comma grouping.
  * Production mass scaled into kilograms (`kg`) and metric tonnes (`T`).
  * Time formatted into clean hours and minutes (`h m`).
* **Unified Period Vocabulary** (`src/lib/period.ts`):
  * Harmonized across all pages: `TODAY`, `SEVEN_DAYS`, `MONTH_TO_DATE`, `QUARTER`, `CUSTOM`.
  * Synchronized with URL parameters for deep-linking and bookmarking.
* **UI Component Library** (`src/design/`):
  * `DataTable`: Fully sortable, searchable, paginated table with one-click **Export to CSV**.
  * `ChartPanel`: Dynamic chart wrapper with an instant **Toggle Chart / Table View** switch.
  * `Drawer`: Slide-over drawer for deep inspection (e.g., machine telemetry) without losing context.
  * `MetricCard`: KPI tiles displaying current metric, target, and comparison period deltas.
* **Application Shell & Navigation** (`src/layout/`):
  * Collapsible sidebar with status badges and mobile-friendly drawer.
  * **Global Command Palette (Ctrl / ⌘ + K)**: Instant keyboard-driven navigation across pages, actions, and individual machine search.
  * Error boundary handling: Page errors isolated so navigation remains functional.

---

### 6. Delivered Application Modules (Pages)

#### 🎛️ Control Tower (`/`)
* **KPI Header Tiles**: Today's total output, achievement percentage, operating efficiency, total downtime, specific energy consumption (kWh/kg), and defect rate.
* **Shift Performance Distribution**: Shift I, Shift II, Shift III visual breakdown.
* **Ranked Production Loss Reasons**: Ranked bar chart highlighting power outages, mechanical failure, raw material shortage, and worker absenteeism with evidence notes.
* **Machines Needing Attention**: Quick-action list of underperforming assets linking straight into machine drawer telemetry.
* **Executive Analyst Brief**: Concise automated assessment of daily operations with 7-day and 30-day gap projections.

#### 🎯 Action Center (`/actions`)
* **Top Operational Priority**: Dedicated card focusing on the #1 bottleneck (e.g., Ring Frame tension issues or Simplex speed restrictions).
* **Where & Why Evidence Panel**: Side-by-side diagnosis correlating affected machine units with root causes.
* **Recommended Interventions**: Prescriptive steps linking directly to affected machines.
* **Interactive Action Tracker**: Tabbed workflow (`All`, `Open`, `In Progress`, `Completed`) with assignee, due date, status tracking, and CSV export.

#### 📊 Production Reconciliation (`/production`)
* **Reconciled Department Figures**: Blowroom through Weaving production data verified to ensure shift sum equals cumulative totals.
* **Discrepancy & Reconciliation Alerts**: Automatic warning banners when shift records fail mathematical validation.
* **Report Date Picker**: Query and verify historical report ingestion dates.
* **Data Lineage Modal**: Trace any cell back to its original uploaded file name, sheet, row, and column.

#### ⚙️ Asset Fleet & Machines (`/assets`)
* **Fleet Register**: Complete machine directory searchable by ID, department, and status.
* **Downtime Decomposition**: Planned maintenance vs unplanned breakdowns.
* **Stoppage & Power Incident Tracking**: Frequency of micro-stoppages and power interruption events.
* **Slide-over Machine Drawer (`?machine=ID`)**: Deep dive into individual speed, temperature, run-hours, and scheduled maintenance dates.

#### ⚖️ Benchmark & Comparison (`/assets/benchmark`)
* **Multi-Machine Benchmarking**: Side-by-side comparison across any combination of machines in the fleet.
* **Radar & Bar Metrics**: Output, efficiency, energy per kg, downtime, and quality score.
* **Head-to-Head Mode**: Automatic head-to-head comparison when two machines are selected.

#### 🔬 Quality Lab (`/quality`)
* **Parameter Tolerance Meters**: Ne Count, CSP, U%, Thin Places, Thick Places, and Neps shown against standard upper/lower specification limits.
* **Defect Rate Trends**: Temporal quality variance tracking.
* **Breakage Analysis**: Warp and weft break frequencies by loom and frame.

#### 👥 Workforce Management (`/workforce`)
* **Department Staffing Matrix**: Required vs actual manpower across Spinning, Preparatory, and Weaving.
* **Absenteeism & Headcount Gaps**: Visualized deficit rankings highlighting areas in urgent need of line balancing.
* **Availability Trends**: Shift-wise attendance rates and contract labor utilization.

#### 💰 Sales & Commercial (`/commercial`)
* **Financial Position**: Monthly turnover, cash collected, and outstanding receivables.
* **Dispatch vs Order Book**: Fabric and yarn order fulfillment rates.
* **Stock Headroom Analysis**: Current finished goods inventory valuation vs safety threshold caps.

#### 📥 Data Imports Hub (`/data`)
* **Drag-and-Drop Batch Uploader**: Staging area for multiple spreadsheets, CSVs, or PDFs.
* **Live Job Monitor**: Real-time progress bar, file count, and status badges.
* **Template Center**: Download pre-configured blank Excel templates or 7-day realistic samples.
* **Import History Log**: Searchable audit log of past imports with status badges and record counts.

#### 🛡️ System Status & Administration (`/admin/system`)
* **Engine Health**: Real-time check on FastAPI backend and SQLite database connectivity.
* **Table Record Counts**: Live telemetry on stored reports, production rows, and downtime entries.
* **Data Freshness Tracker**: Timestamp audit verifying the latest uploaded data records.

---

### 7. Deployment & DevOps Infrastructure
* **Docker Multi-Stage Setup** (`docker-compose.yml`):
  * `ai-factory-backend`: Containerized FastAPI application using Python 3.11-slim, persistent volume mounts (`factory_data`, `factory_reports`), automated curl healthcheck on `/api/v1/health`.
  * `ai-factory-frontend`: Production Nginx web server container serving the optimized Vite React build on port 5173.
* **Environment Configuration**: Pre-configured `.env.example` templates for both frontend and backend.
* **Repository Sanitation**: Robust `.gitignore` covering SQLite databases, temporary uploads, cache files, and virtual environments.

---

## 📂 Repository File Structure

```
Textile-/
├── .gitignore                          # Git ignore rules (DB, cache, uploads, node_modules)
├── README.md                           # Quick start developer onboarding guide
├── WHAT_WE_BUILT.md                    # Detailed architectural & capability documentation
├── docker-compose.yml                  # Production Docker multi-container definition
├── sample_synthetic_data.xlsx          # Pre-packaged 7-day multi-sheet test workbook
├── uploaded_reports/                   # Staging directory for uploaded documents
│
├── docs/
│   └── REDESIGN.md                     # Architectural evaluation & frontend modernization spec
│
├── backend/
│   ├── Dockerfile                      # Backend container configuration
│   ├── requirements.txt                # Python dependencies (FastAPI, SQLAlchemy, Pandas, etc.)
│   ├── .env.example                    # Backend environment configuration
│   └── app/
│       ├── main.py                     # FastAPI application entry point & CORS configuration
│       ├── core/                       # App settings, logging, and constants
│       ├── db/                         # SQLAlchemy session factory & Base model
│       ├── models/                     # Database models (Report, Production, Template, etc.)
│       ├── schemas/                    # Pydantic v2 validation schemas
│       ├── api/v1/                     # REST API routers (overview, production, machines, etc.)
│       └── services/
│           ├── ingestion/              # Extractor, Normalizer, and Job processing
│           ├── template/               # Template Builder, Spec, Importer & Factory Data
│           ├── overview_service.py     # Control Tower service
│           ├── production_service.py   # Production reconciliation service
│           ├── machines_service.py     # Fleet and maintenance service
│           ├── machine_comparison_service.py # Machine benchmark service
│           ├── manpower_quality_service.py   # HR and QA service
│           ├── revenue_loss_service.py # Commercial and financial service
│           └── decision_center_service.py    # Root-cause analysis service
│
└── frontend/
    ├── Dockerfile                      # Frontend container configuration
    ├── package.json                    # Node dependencies (React 18, Vite, React Query, Lucide)
    ├── vite.config.ts                  # Vite bundler settings
    ├── tailwind.config.js              # Tailwind styling config
    └── src/
        ├── main.tsx                    # React DOM entry point with QueryClient & Router
        ├── index.css                   # Design tokens, CSS variables, and light/dark theme rules
        ├── app/
        │   ├── router.tsx              # React Router v6 browser route definitions
        │   └── state.ts                # App-level UI state management
        ├── layout/
        │   ├── AppShell.tsx            # Main application layout wrapper
        │   ├── Sidebar.tsx             # Collapsible primary navigation
        │   ├── PageHeader.tsx          # Unified header with period selector
        │   ├── CommandPalette.tsx      # Ctrl+K search and keyboard navigation
        │   └── AshokLogo.tsx           # Custom branded SVG logo
        ├── design/
        │   ├── ui.tsx                  # Buttons, Cards, Badges, Tabs, EmptyStates, Progress
        │   ├── DataTable.tsx           # Sortable, searchable table with CSV export
        │   ├── ChartPanel.tsx          # Chart wrapper with Chart/Table switch
        │   └── Drawer.tsx              # Slide-over inspector drawer
        ├── features/
        │   ├── control-tower/          # Executive Control Tower dashboard
        │   ├── actions/                # Action Center & issue tracking
        │   ├── production/             # Reconciled production analytics
        │   ├── assets/                 # Fleet register, Benchmark & Machine drawer
        │   ├── quality/                # Quality testing parameters & break rates
        │   ├── workforce/              # Staffing gaps & attendance trends
        │   ├── commercial/             # Revenue, cash collections & stock headroom
        │   ├── data/                   # File batch uploader & template center
        │   └── admin/                  # System status & database health monitor
        ├── api/
        │   ├── client.ts               # Axios HTTP client configuration
        │   └── queries.ts              # TanStack React Query query hooks
        ├── lib/
        │   ├── format.ts               # Indian currency, weight, and duration formatters
        │   ├── period.ts               # Period enumeration and URL syncing
        │   └── links.ts                # Deep-link routing helpers
        └── types/                      # TypeScript schemas mirroring backend models
```

---

## 📈 Summary of Achievements & Immediate Value

1. **Zero Fake Data Fallbacks**: The system cleanly separates synthetic demo baselines from real imported data, with transparent error states and retry buttons rather than invented metrics.
2. **Strict Shift Reconciliation**: Ensures executive metrics respect physical factory realities ($\text{Shift I} + \text{Shift II} + \text{Shift III} = \text{Daily Total}$).
3. **Turnkey Spreadsheet Ingestion**: Any factory department can download the pre-formatted Excel template, input their shift data, and upload it to immediately update their domain's analytics.
4. **Universal Keyboard & URL Navigation**: Complete deep linking for machines, timeframes, and tabs, paired with a command palette (`Ctrl + K`) for high-speed plant management.
5. **Production Docker Deployment**: Fully containerized and ready to deploy to any cloud VM or on-premises factory server with one command (`docker-compose up -d`).

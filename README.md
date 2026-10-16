# 🏭 AI FACTORY MANAGER — Ashok Textiles

An AI-powered textile factory management, real-data report ingestion, and decision-support system built from first principles.

---

## 🌟 Key Features

1. **Universal Report Data Ingestion Engine**:
   - Accepts multi-department factory reports in **XLSX, XLS, CSV, PDF, JPG, JPEG, PNG**.
   - Section-aware auto-parsing for `Carding`, `Draw Frame`, `Simplex`, `Ring Frame`, `Airjet`, `Vortex`, `Weaving`, `Combing`, `Blowroom`, and custom factory sections.
   - Dynamic report date & mill unit detection with duplicate protection and SHA256 checksum verification.

2. **Asynchronous Multi-File Job Processing Pipeline**:
   - Supports selecting or drag-and-dropping multiple report files simultaneously.
   - Non-blocking job queue with live progress polling (`progress_pct`, `processed_count`, file status badges).
   - Fault-tolerant batch processing.

3. **Data Template (updates every page)**:
   - In **Upload Reports**, click **Template** to download an Excel file with one sheet per data set (`Machine_Data`, `Manpower`, `Quality`, `Business`, `Stock`, `Actions`) plus an `Instructions` sheet listing every field. **Sample** downloads the same file pre-filled with 7 days of example data.
   - Fill it in and upload it. Overview, Production, Machines & Downtime, Machine Comparison, Manpower & Quality, Revenue & Loss and Decision Center all recalculate from it.
   - A page only switches from the built-in synthetic data once you upload data for it (e.g. a template with only a `Manpower` sheet changes only the Manpower & Quality page). A new template replaces earlier template data for the same dates.
   - Field definitions live in `backend/app/services/template/template_spec.py`; the importer is `template_importer.py`.

4. **Reconciled Production Dashboard**:
   - 100% data-driven metrics with zero hardcoded/mock fallbacks.
   - Strict shift & department reconciliation ($\sum \text{Shift Actuals} = \text{Cumulative Actual}$, $\sum \text{Shift Targets} = \text{Cumulative Target}$, $\sum \text{Shift Gaps} = \text{Cumulative Gap}$).
   - Source-driven Downtime and Production Factors (`Data unavailable` handling for omitted metrics).

5. **Weaving module (sample data)**:
   - `/weaving` has an Owner view (verdict, decisions with ₹ at stake, where money leaks, style profit) and a Manager view (looms stopped now, shifts, problem looms, open actions), plus Looms, Stoppages, Fabric quality, Styles & profit and People & maintenance tabs.
   - It currently runs on deterministic **mock data** (`backend/app/services/weaving_service.py`) and shows a "Sample data" banner. Replace `_build_dataset` with a real loader when weaving reports are available.

6. **Data Lineage Traceability**:
   - End-to-end auditability mapping every KPI back to `source_file`, `source_sheet`, `source_row`, and `source_column`.

---

## 🐳 Run with Docker

```bash
cp .env.example .env     # set POSTGRES_PASSWORD and SECRET_KEY first (see the file)
docker compose up -d --build
```

- App: http://localhost:5173 (nginx serves the UI and proxies `/api/` to the backend)
- API docs: http://localhost:8000/api/v1/docs
- Data lives in PostgreSQL (`postgres_data` volume) and the `factory_reports` volume (uploads); `factory_data` still holds the old SQLite file for the one-time copy. `docker compose down` keeps them; **`-v` deletes the database**.
- Migrations run in the backend entrypoint. Backup, restore, migration and the SQLite-to-PostgreSQL copy are in [docs/database.md](docs/database.md).
- The backend drops to a non-root user at start-up. `.dockerignore` files keep `uploaded_reports/`, `.env` and `node_modules` out of the images.

---

## 🏗️ System Architecture

```
FRONTEND (React + Vite + TypeScript + Tailwind CSS)
    ↓ REST API (Axios Async Client)
BACKEND (FastAPI + Pydantic v2 + SQLAlchemy + Alembic + PostgreSQL)
    ↓ Weaving analytics: SQL + statistics -> evidence-backed findings (docs/weaving-intelligence.md)
    ↓ Processing Engine
DATA INGESTION (Pandas + OpenPyXL + PyPDF + Pillow + Normalizer)
```

---

## 🚀 Quick Start Guide for Collaborators

### Prerequisites
- **Python**: `3.10` or higher
- **Node.js**: `18.0` or higher (with `npm`)

---

### 1. Backend Setup & Server Start

```bash
# Navigate to the backend folder
cd backend

# (Optional but recommended) Create and activate a virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install Python dependencies (requirements-dev.txt adds the test tools)
pip install -r requirements-dev.txt

# Configure the database: copy the template and set POSTGRES_PASSWORD (or DATABASE_URL)
cp .env.example .env

# Launch FastAPI development server (applies migrations on start-up when AUTO_MIGRATE=true)
python -m uvicorn app.main:app --reload --port 8000

# Optional: DEMONSTRATION weaving data for development (refuses to run when ENVIRONMENT=production)
python -m app.weaving.seed demo --days 21        # add --reset-demo to reload after a data change
```

You need a PostgreSQL 16 server (for example `docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=... postgres:16-alpine`).
If you have an old `ai_factory_manager.db`, copy it across with the tool described in [docs/database.md](docs/database.md): changing the database URL does not move data.

- **Backend API**: `http://localhost:8000`
- **Interactive Swagger Documentation**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

### 2. Frontend Setup & App Start

```bash
# Open a new terminal and navigate to the frontend folder
cd frontend

# Install Node dependencies
npm install

# (Optional) Copy environment variables template
cp .env.example .env

# Launch Vite development server
npm run dev
```

- **Frontend App**: [http://localhost:5173](http://localhost:5173)

---

## 📁 Repository Structure

```
Textile/
├── docker-compose.yml              # Backend + frontend (nginx) stack
├── backend/                        # FastAPI backend
│   ├── app/
│   │   ├── api/v1/                 # Endpoints (production, ingestion, overview, weaving, ...)
│   │   ├── core/ db/ models/       # Config, database, migrations runner, ORM models
│   │   ├── weaving/                # Weaving schema, analytics (metrics, investigations), demo seed
│   │   ├── schemas/                # Pydantic schemas
│   │   └── services/               # Ingestion, template and legacy module services
│   ├── alembic/ tests/             # Migrations; test suite
│   ├── uploaded_reports/           # Upload staging (git-ignored; may hold employee data)
│   ├── Dockerfile, requirements.txt, .env.example
├── frontend/                       # React + Vite + TypeScript
│   └── src/
│       ├── app/ layout/ design/    # Router, shell, design system and charts
│       ├── features/               # One folder per page group (weaving, production, quality, ...)
│       ├── api/ lib/ types/        # React Query hooks, formatters, backend types
│   ├── Dockerfile, nginx.conf
└── docs/                           # database.md, weaving-intelligence.md, REDESIGN.md
```

---

## 🧪 Verification & Build Commands

### Frontend Type Check & Production Build
```bash
cd frontend
npm run build
```

### Backend tests
```bash
createdb textile_test        # a DEDICATED database; its name must end in _test (the suite recreates its schema)
cd backend
TEST_DATABASE_URL="postgresql+psycopg://USER:PASSWORD@localhost:5432/textile_test" python -m pytest
```
Without `TEST_DATABASE_URL` the PostgreSQL tests are skipped (and reported as skipped).

---

## 📜 Key API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/ingestion/upload-job` | Create an async job to ingest multiple report files |
| `GET` | `/api/v1/ingestion/job/{job_id}` | Poll progress status for an active ingestion job |
| `GET` | `/api/v1/production` | Get reconciled production metrics for date and unit |
| `GET` | `/api/v1/production/lineage` | Trace data lineage for production metrics back to source file/row |
| `POST` | `/api/v1/auth/login` | Sign in; every weaving route needs the returned bearer token |
| `GET` | `/api/v1/weaving/pages/{page}` | One payload per sidebar page (command, owner, production, stoppages, machines, workforce, orders, scheduler, insights, quality, cockpit, handover, maintenance, actions, compare), computed from the database for the caller's role |
| `GET` | `/api/v1/weaving/analytics/{production,stoppages,quality}?group_by=` | Metrics by loom, style, beam, shift, day, cause... |
| `GET` | `/api/v1/weaving/investigations/{findings,priorities}` | Evidence-backed findings and "what to focus on today" for the caller's role |
| `GET` | `/api/v1/weaving/events/stops`, `/inspections` | Paginated event lists |
| `GET` | `/api/v1/weaving/compare/run` | Compare looms, styles, shifts, yarn lots, suppliers side by side (tested differences) |
| `POST` | `/api/v1/weaving/scheduler/decision` | Approve or reject the AI-proposed schedule (owner / weaving manager). Approval records it and raises actions; it moves no loom |
| `POST` | `/api/v1/weaving/actions`, `/notes` | Record actions (approval rules apply) and shift notes |
| `GET` | `/api/v1/health` | System health check and database connectivity status |

---

## 👥 Collaborator Notes
- `.gitignore` ensures that database files (`ai_factory_manager.db`), database dumps (`*.dump`, `backups/`), python `__pycache__`, virtual environments (`.venv`), and `node_modules/` remain uncommitted.
- Environment templates are committed as `.env.example` in both `backend/` and `frontend/`.
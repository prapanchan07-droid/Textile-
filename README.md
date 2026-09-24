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

5. **Data Lineage Traceability**:
   - End-to-end auditability mapping every KPI back to `source_file`, `source_sheet`, `source_row`, and `source_column`.

---

## 🏗️ System Architecture

```
FRONTEND (React + Vite + TypeScript + Tailwind CSS)
    ↓ REST API (Axios Async Client)
BACKEND (FastAPI + Pydantic v2 + SQLAlchemy + SQLite)
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

# Install Python dependencies
pip install -r requirements.txt

# (Optional) Copy environment variables template
cp .env.example .env

# Launch FastAPI development server
python -m uvicorn app.main:app --reload --port 8000
```

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
├── .gitignore                      # Git ignore rule definitions (Python, Node, DB, OS)
├── README.md                       # Developer & Collaborator Documentation
├── uploaded_reports/               # Staging folder for uploaded factory report files
│   └── .gitkeep
├── backend/                        # FastAPI Backend Application
│   ├── app/
│   │   ├── api/v1/                 # Endpoints (production, ingestion, overview, decision center)
│   │   ├── core/                   # Config, logging, exceptions
│   │   ├── db/                     # Database session & tables setup
│   │   ├── models/                 # SQLAlchemy ORM schemas
│   │   ├── schemas/                # Pydantic data schemas
│   │   └── services/               # Ingestion Service, Extractor, Normalizer, Production Service
│   ├── .env.example                # Backend environment variable template
│   ├── requirements.txt            # Python dependencies list
│   └── main.py                     # ASGI App Entrypoint
└── frontend/                       # React + Vite Frontend Application
    ├── src/
    │   ├── components/             # Header, Modals, Production UI, KPI Cards
    │   ├── pages/                  # Dashboard pages (Production, Overview, Decision Center)
    │   ├── services/               # API clients & backend communication
    │   └── types/                  # TypeScript interfaces & types
    ├── package.json                # Node scripts & npm dependencies
    ├── vite.config.ts              # Vite bundler configuration
    ├── tailwind.config.js          # Tailwind CSS styling config
    └── .env.example                # Frontend environment variable template
```

---

## 🧪 Verification & Build Commands

### Frontend Type Check & Production Build
```bash
cd frontend
npm run build
```

### Run Clean Database & Ingestion Test
```bash
# From workspace root
python -c "from app.db.session import SessionLocal; print('DB connection verified!')"
```

---

## 📜 Key API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/ingestion/upload-job` | Create an async job to ingest multiple report files |
| `GET` | `/api/v1/ingestion/job/{job_id}` | Poll progress status for an active ingestion job |
| `GET` | `/api/v1/production` | Get reconciled production metrics for date and unit |
| `GET` | `/api/v1/production/lineage` | Trace data lineage for production metrics back to source file/row |
| `GET` | `/api/v1/health` | System health check and database connectivity status |

---

## 👥 Collaborator Notes
- `.gitignore` ensures that database files (`ai_factory_manager.db`), python `__pycache__`, virtual environments (`.venv`), and `node_modules/` remain uncommitted.
- Environment templates are committed as `.env.example` in both `backend/` and `frontend/`.
import os
import hashlib
import uuid
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.ingestion import (
    ReportRecord,
    ProductionRecord,
    DowntimeRecord,
    QualityRecord,
    EnergyRecord,
    ManpowerRecord
)
from app.services.ingestion.extractor import Extractor
from app.services.ingestion.normalizer import Normalizer
from app.services.template.template_importer import TemplateImporter
from app.core.logging import logger

UPLOAD_STORAGE_DIR = "uploaded_reports"

# In-memory Async Job Store for real-time multi-file status tracking
JOBS_STORE: Dict[str, Dict[str, Any]] = {}

class IngestionJobManager:
    @staticmethod
    def create_job(total_files: int) -> str:
        job_id = str(uuid.uuid4())
        JOBS_STORE[job_id] = {
            "job_id": job_id,
            "status": "PROCESSING",  # PROCESSING, COMPLETED, FAILED
            "total_files": total_files,
            "processed_count": 0,
            "success_count": 0,
            "failed_count": 0,
            "duplicate_count": 0,
            "progress_pct": 0,
            "created_at": datetime.utcnow().isoformat(),
            "file_statuses": []
        }
        return job_id

    @staticmethod
    def get_job(job_id: str) -> Optional[Dict[str, Any]]:
        return JOBS_STORE.get(job_id)

    @staticmethod
    def run_job_in_background(
        job_id: str,
        files_payload: List[Tuple[bytes, str]],
        report_type_override: Optional[str] = None,
        date_override: Optional[str] = None,
        force_replace: bool = False
    ):
        thread = threading.Thread(
            target=IngestionJobManager._process_job_worker,
            args=(job_id, files_payload, report_type_override, date_override, force_replace),
            daemon=True
        )
        thread.start()

    @staticmethod
    def _process_job_worker(
        job_id: str,
        files_payload: List[Tuple[bytes, str]],
        report_type_override: Optional[str],
        date_override: Optional[str],
        force_replace: bool
    ):
        job = JOBS_STORE.get(job_id)
        if not job:
            return

        total = len(files_payload)

        for idx, (content, filename) in enumerate(files_payload, 1):
            file_status_entry = {
                "filename": filename,
                "status": "PROCESSING",
                "message": "Processing file...",
                "report_type": None,
                "report_date": None
            }
            job["file_statuses"].append(file_status_entry)

            db: Session = SessionLocal()
            try:
                res = IngestionService.process_upload(
                    db=db,
                    file_bytes=content,
                    filename=filename,
                    report_type_override=report_type_override,
                    date_override=date_override,
                    force_replace=force_replace
                )

                if res.get("status") == "SUCCESS":
                    file_status_entry["status"] = "SUCCESS"
                    file_status_entry["message"] = res.get("message") or "Report processed successfully."
                    file_status_entry["report_type"] = res.get("final_report_type")
                    file_status_entry["report_date"] = res.get("report_date")
                    job["success_count"] += 1
                elif res.get("status") == "DUPLICATE":
                    file_status_entry["status"] = "DUPLICATE"
                    file_status_entry["message"] = "Report already imported."
                    file_status_entry["report_type"] = res.get("existing_report", {}).get("report_type")
                    file_status_entry["report_date"] = res.get("existing_report", {}).get("report_date")
                    job["duplicate_count"] += 1
                else:
                    file_status_entry["status"] = "FAILED"
                    file_status_entry["message"] = res.get("message", "Processing failed.")
                    job["failed_count"] += 1

            except Exception as e:
                logger.error(f"Failed to process {filename} in job {job_id}: {e}")
                file_status_entry["status"] = "FAILED"
                file_status_entry["message"] = f"Could not process {filename}. {str(e)}"
                job["failed_count"] += 1
            finally:
                db.close()

            job["processed_count"] = idx
            job["progress_pct"] = int((idx / total) * 100)

        job["status"] = "COMPLETED"


class IngestionService:
    @staticmethod
    def calculate_file_hash(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def process_upload(
        db: Session,
        file_bytes: bytes,
        filename: str,
        report_type_override: Optional[str] = None,
        date_override: Optional[str] = None,
        force_replace: bool = False
    ) -> Dict[str, Any]:
        """
        Full real data ingestion pipeline:
        File validation -> SHA256 hash & type check -> Extraction -> Normalization -> Validation -> Database Storage
        """
        os.makedirs(UPLOAD_STORAGE_DIR, exist_ok=True)
        file_hash = IngestionService.calculate_file_hash(file_bytes)

        # 1. Exact file hash duplicate check
        existing_report = db.query(ReportRecord).filter(ReportRecord.file_hash == file_hash).first()
        if existing_report and not force_replace:
            return {
                "status": "DUPLICATE",
                "message": "Report already imported.",
                "existing_report": {
                    "id": existing_report.id,
                    "filename": existing_report.filename,
                    "report_type": existing_report.report_type,
                    "report_date": existing_report.report_date,
                    "upload_timestamp": existing_report.upload_timestamp.isoformat()
                }
            }

        # If force replace, delete old report and cascading records
        if existing_report and force_replace:
            TemplateImporter.purge_report(db, existing_report.id)
            db.delete(existing_report)
            db.commit()

        # Save physical file to disk
        file_id = str(uuid.uuid4())
        saved_filename = f"{file_id}_{filename}"
        saved_filepath = os.path.join(UPLOAD_STORAGE_DIR, saved_filename)
        with open(saved_filepath, "wb") as f:
            f.write(file_bytes)

        # Data template (downloaded from the app and filled in): import directly into every dashboard table
        if os.path.splitext(filename)[1].lower() == ".xlsx" and TemplateImporter.is_template(saved_filepath):
            try:
                return TemplateImporter.import_file(db, file_id, file_hash, filename, saved_filepath)
            except Exception:
                db.rollback()
                raise

        # Extract content
        records, sheet_names, extracted_date, extracted_unit = Extractor.extract_from_file(saved_filepath, filename)
        headers = list(records[0].keys()) if records else []

        # Detect Report Type & Confidence
        detected_type, confidence = Normalizer.detect_report_type(filename, sheet_names, headers)
        final_type = report_type_override if report_type_override else detected_type
        final_date = date_override if date_override else extracted_date

        # Check for same type + date + filename duplicate if hash differed slightly
        existing_same_type_date = db.query(ReportRecord).filter(
            ReportRecord.report_type == final_type,
            ReportRecord.report_date == final_date,
            ReportRecord.filename == filename
        ).first()

        if existing_same_type_date and not force_replace and not existing_report:
            return {
                "status": "DUPLICATE",
                "message": "Report already imported.",
                "existing_report": {
                    "id": existing_same_type_date.id,
                    "filename": existing_same_type_date.filename,
                    "report_type": existing_same_type_date.report_type,
                    "report_date": existing_same_type_date.report_date,
                    "upload_timestamp": existing_same_type_date.upload_timestamp.isoformat()
                }
            }

        if existing_same_type_date and force_replace:
            db.delete(existing_same_type_date)
            db.commit()

        # Create Report Record
        report_rec = ReportRecord(
            id=file_id,
            file_hash=file_hash,
            filename=filename,
            file_path=saved_filepath,
            report_type=final_type,
            confidence_score=confidence,
            status="PROCESSED",
            report_date=final_date,
            upload_timestamp=datetime.utcnow()
        )
        db.add(report_rec)

        # Normalize & Insert records according to Report Type
        inserted_counts = {
            "production": 0,
            "downtime": 0,
            "quality": 0,
            "energy": 0,
            "manpower": 0
        }
        validation_warnings = []

        shift_gaps_sum = 0.0
        reported_total_gap = 0.0

        for r in records:
            # Check summary row filter
            row_vals_str = " ".join([str(v).upper() for v in r.values()])
            is_summary_row = "TOTAL" in row_vals_str or "SUM" in row_vals_str
            has_granular_shifts = any(Normalizer.parse_shift(other.get("shift")) for other in records if str(other.get("department")) == str(r.get("department")))
            if is_summary_row and has_granular_shifts:
                continue

            shift_val = Normalizer.parse_shift(r.get("shift"))
            actual_kg = Normalizer.parse_number(r.get("actual_production"))
            target_kg = Normalizer.parse_number(r.get("target_production"))
            gap_kg = Normalizer.parse_number(r.get("production_gap"))
            if target_kg > 0 and gap_kg == 0.0:
                gap_kg = max(0.0, target_kg - actual_kg)
            ach_pct = round((actual_kg / target_kg * 100), 1) if target_kg > 0 else 0.0

            row_unit = str(r.get("unit")) if r.get("unit") else extracted_unit

            dept_str = str(r.get("department") or r.get("machine_type") or "").upper()
            raw_mtype = str(r.get("machine_type")) if r.get("machine_type") else None
            if not raw_mtype:
                if "CARD" in dept_str:
                    raw_mtype = "Carding"
                elif "DRAW" in dept_str:
                    raw_mtype = "Draw Frame"
                elif "SIMPLEX" in dept_str or "SPEED" in dept_str:
                    raw_mtype = "Simplex"
                elif "RING" in dept_str or "SPIN" in dept_str:
                    raw_mtype = "Ring Frame"
                elif "AIRJET" in dept_str or "WEAV" in dept_str:
                    raw_mtype = "Airjet"
                elif "VORTEX" in dept_str:
                    raw_mtype = "Vortex"
                else:
                    raw_mtype = "UNKNOWN"

            # 1. Insert Production Record if production fields exist
            if actual_kg > 0 or target_kg > 0:
                prod = ProductionRecord(
                    id=str(uuid.uuid4()),
                    source_report_id=file_id,
                    report_date=final_date,
                    shift=shift_val,
                    department=str(r.get("department")) if r.get("department") else None,
                    unit=row_unit,
                    machine_type=raw_mtype,
                    machine_id=str(r.get("machine_id")) if r.get("machine_id") else None,
                    actual_kg=actual_kg,
                    target_kg=target_kg,
                    gap_kg=gap_kg,
                    achievement_pct=ach_pct,
                    source_sheet=str(r.get("_source_sheet")) if r.get("_source_sheet") else "Sheet1",
                    source_row=int(r.get("_source_row")) if r.get("_source_row") else None,
                    source_column=str(r.get("_source_column")) if r.get("_source_column") else "Main"
                )
                db.add(prod)
                inserted_counts["production"] += 1
                if shift_val:
                    shift_gaps_sum += gap_kg
                else:
                    reported_total_gap = gap_kg

            # 2. Insert Downtime Record if downtime fields exist
            raw_dt_min = r.get("downtime_minutes")
            downtime_min = Normalizer.parse_number(raw_dt_min) if raw_dt_min is not None else None
            loss_kg = Normalizer.parse_number(r.get("loss_kg"))
            reason_cat = str(r.get("reason_category") or r.get("remarks") or "").strip()

            if loss_kg <= 0 and gap_kg > 0 and reason_cat:
                loss_kg = gap_kg

            if (downtime_min is not None and downtime_min > 0) or loss_kg > 0 or (reason_cat and reason_cat.upper() not in ["NONE", "NAN", "NULL", ""]):
                if not reason_cat:
                    reason_cat = "Machine Downtime"
                dt = DowntimeRecord(
                    id=str(uuid.uuid4()),
                    source_report_id=file_id,
                    report_date=final_date,
                    shift=shift_val,
                    machine_id=str(r.get("machine_id")) if r.get("machine_id") else None,
                    machine_type=raw_mtype,
                    downtime_minutes=downtime_min,
                    loss_kg=loss_kg,
                    reason_category=reason_cat,
                    remarks=str(r.get("remarks")) if r.get("remarks") else None
                )
                db.add(dt)
                inserted_counts["downtime"] += 1

            # 3. Insert Quality Record
            if r.get("yarn_count") or r.get("quality_score"):
                q = QualityRecord(
                    id=str(uuid.uuid4()),
                    source_report_id=file_id,
                    report_date=final_date,
                    shift=shift_val,
                    yarn_count=str(r.get("yarn_count")) if r.get("yarn_count") else None,
                    quality_score=Normalizer.parse_number(r.get("quality_score"), 100.0),
                    defect_rate=Normalizer.parse_number(r.get("defect_rate"), 0.0),
                    warp_breaks=int(Normalizer.parse_number(r.get("warp_breaks"), 0)),
                    weft_breaks=int(Normalizer.parse_number(r.get("weft_breaks"), 0))
                )
                db.add(q)
                inserted_counts["quality"] += 1

            # 4. Insert Energy Record
            if r.get("kwh_consumed") or r.get("energy_per_kg"):
                eng = EnergyRecord(
                    id=str(uuid.uuid4()),
                    source_report_id=file_id,
                    report_date=final_date,
                    shift=shift_val,
                    kwh_consumed=Normalizer.parse_number(r.get("kwh_consumed")),
                    energy_per_kg=Normalizer.parse_number(r.get("energy_per_kg"))
                )
                db.add(eng)
                inserted_counts["energy"] += 1

            # 5. Insert Manpower Record
            if r.get("planned_manpower") or r.get("actual_manpower"):
                p_mp = int(Normalizer.parse_number(r.get("planned_manpower")))
                a_mp = int(Normalizer.parse_number(r.get("actual_manpower")))
                mp = ManpowerRecord(
                    id=str(uuid.uuid4()),
                    source_report_id=file_id,
                    report_date=final_date,
                    shift=shift_val,
                    department=str(r.get("department")) if r.get("department") else None,
                    planned_count=p_mp,
                    actual_count=a_mp,
                    gap_count=max(0, p_mp - a_mp)
                )
                db.add(mp)
                inserted_counts["manpower"] += 1

        # Check gap reconciliation
        if shift_gaps_sum > 0 and reported_total_gap > 0 and abs(shift_gaps_sum - reported_total_gap) > 0.1:
            validation_warnings.append(
                f"Gap reconciliation warning: Sum of shift gaps ({shift_gaps_sum:.1f} kg) does not equal reported total gap ({reported_total_gap:.1f} kg)."
            )

        db.commit()

        return {
            "status": "SUCCESS",
            "message": "Report uploaded and processed successfully.",
            "report_id": file_id,
            "filename": filename,
            "detected_report_type": detected_type,
            "final_report_type": final_type,
            "confidence_score": confidence,
            "report_date": final_date,
            "inserted_counts": inserted_counts,
            "validation_warnings": validation_warnings
        }

    @staticmethod
    def get_upload_history(db: Session) -> List[Dict[str, Any]]:
        reports = db.query(ReportRecord).order_by(ReportRecord.upload_timestamp.desc()).all()
        return [
            {
                "id": r.id,
                "filename": r.filename,
                "report_type": r.report_type,
                "confidence_score": r.confidence_score,
                "status": r.status,
                "report_date": r.report_date,
                "upload_timestamp": r.upload_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            }
            for r in reports
        ]

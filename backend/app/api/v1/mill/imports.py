"""Report imports: upload + preview, commit in the background, history, issues, reconciliation."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.v1.mill.common import Page, PageSize, ok, paginate
from app.core.exceptions import NotFoundException, ValidationException
from app.core.logging import logger
from app.db.session import SessionLocal, get_db
from app.mill import audit
from app.mill.importers import FORMATS
from app.mill.importers.service import ImportRefused, commit, preview
from app.mill.models import ImportBatch, ImportIssue
from app.models.user import User

router = APIRouter(prefix="/imports", tags=["Imports"])


def _batch(b: ImportBatch, full: bool = False) -> dict:
    out = {
        "id": b.id, "filename": b.filename, "status": b.status, "source_format": b.source_format,
        "format_label": FORMATS.get(b.source_format or "", None), "size_bytes": b.size_bytes, "sha256": b.sha256,
        "period_start": b.period_start, "period_end": b.period_end, "records_parsed": b.records_parsed,
        "records_inserted": b.records_inserted, "records_updated": b.records_updated, "records_unchanged": b.records_unchanged,
        "error_count": b.error_count, "warning_count": b.warning_count, "error": b.error, "created_at": b.created_at,
        "committed_at": b.committed_at, "parser_version": b.parser_version,
        "reconciliation_summary": {s: sum(1 for c in (b.reconciliation or []) if c["status"] == s) for s in ("MATCH", "MISMATCH", "NOT_COMPARABLE")},
    }
    if full:
        out["summary"] = b.summary
        out["reconciliation"] = b.reconciliation
    return out


@router.get("")
def history(page: int = Page, page_size: int = PageSize, db: Session = Depends(get_db)):
    return ok(paginate(db, select(ImportBatch).order_by(ImportBatch.id.desc()), page, page_size, _batch))


@router.get("/formats")
def formats():
    return ok([{"code": k, "label": v} for k, v in FORMATS.items()])


@router.post("/preview")
async def upload_and_preview(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    content = await file.read()
    if not content:
        raise ValidationException("The file is empty")
    try:
        b = preview(db, content, file.filename or "upload", user.id)
    except ImportRefused as e:
        raise ValidationException(str(e))
    audit.record(db, user.id, "IMPORT_PREVIEW", "import_batch", b.id, after={"filename": b.filename, "status": b.status})
    db.commit()
    return ok(_batch(b, full=True))


@router.get("/{batch_id}")
def detail(batch_id: int, db: Session = Depends(get_db)):
    b = db.get(ImportBatch, batch_id)
    if b is None:
        raise NotFoundException("Import not found")
    return ok(_batch(b, full=True))


@router.get("/{batch_id}/issues")
def issues(batch_id: int, severity: Optional[str] = None, page: int = Page, page_size: int = PageSize, db: Session = Depends(get_db)):
    q = select(ImportIssue).where(ImportIssue.batch_id == batch_id)
    if severity:
        q = q.where(ImportIssue.severity == severity.upper())
    q = q.order_by(ImportIssue.id)
    return ok(paginate(db, q, page, page_size, lambda i: {
        "id": i.id, "severity": i.severity, "code": i.code, "message": i.message, "sheet": i.sheet, "row": i.row, "column": i.column, "raw_value": i.raw_value}))


def _commit_job(batch_id: int, user_id: str) -> None:
    from app.mill.alerts.engine import evaluate_all

    with SessionLocal() as db:
        b = db.get(ImportBatch, batch_id)
        b.status = "PREVIEWED"  # commit() requires it; PROCESSING was only shown to the UI
        try:
            commit(db, b)
            audit.record(db, user_id, "IMPORT_COMMIT", "import_batch", b.id, after={"inserted": b.records_inserted, "updated": b.records_updated})
            db.commit()
        except Exception as e:
            db.rollback()
            b = db.get(ImportBatch, batch_id)
            b.status, b.error = "FAILED", f"{type(e).__name__}: {e}"
            db.commit()
            logger.error(f"Import {batch_id} failed: {e}", exc_info=True)
            return
        try:
            evaluate_all(db)
            db.commit()
        except Exception as e:  # the import stands even if alert evaluation fails
            db.rollback()
            logger.error(f"Alert evaluation after import {batch_id} failed: {e}", exc_info=True)


@router.post("/{batch_id}/commit")
def commit_batch(batch_id: int, tasks: BackgroundTasks, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    b = db.get(ImportBatch, batch_id)
    if b is None:
        raise NotFoundException("Import not found")
    if b.status != "PREVIEWED":
        raise ValidationException(f"This import is {b.status}; only a previewed import can be committed")
    b.status = "PROCESSING"
    db.commit()
    tasks.add_task(_commit_job, batch_id, user.id)
    return ok(_batch(b))


@router.post("/{batch_id}/discard")
def discard(batch_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    b = db.get(ImportBatch, batch_id)
    if b is None:
        raise NotFoundException("Import not found")
    if b.status != "PREVIEWED":
        raise ValidationException("Only a previewed import can be discarded")
    b.status = "DISCARDED"
    audit.record(db, user.id, "IMPORT_DISCARD", "import_batch", b.id)
    db.commit()
    return ok(_batch(b))

"""
Import workflow: upload -> preview -> commit.

  * `preview` stores the original file (unchanged), parses it and records a PREVIEWED batch with its issues and
    reconciliation checks, plus what a commit would insert / update / leave unchanged. Nothing else is written.
  * `commit` re-parses the stored file and writes looms, styles, raw rows and shift records in one transaction.
    It is idempotent: the same file twice is refused as a duplicate, and re-importing overlapping data updates
    records in place (one record per loom, date, shift and source) instead of adding copies.
  * A second file of the same report fills in what the first lacked (Tsudakoma PICK then MTR): non-empty values
    are merged; a changed value is recorded as a REVISED issue so the history stays visible.
"""
from __future__ import annotations

import hashlib
import os
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.mill import constants as C
from app.mill.importers import FORMATS, UnknownFormat, detect_and_parse
from app.mill.importers.base import PARSER_VERSION, ParseResult, Record
from app.mill.importers.readers import UnsupportedFile, read_workbook
from app.mill.models import ImportBatch, ImportIssue, Loom, RawSourceRow, ShiftProduction, Style

VALUE_FIELDS = (
    "style_code", "rpm", "efficiency_pct", "loom_efficiency_pct", "kilopicks", "meters", "warp_stops", "weft_stops",
    "other_stops", "total_stops", "run_min", "stop_min", "warp_stop_min", "weft_stop_min", "air_nm3", "operator_name",
)
MAX_REVISION_ISSUES = 200


class ImportRefused(ValueError):
    pass


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _store(content: bytes, digest: str, filename: str) -> str:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9._ -]", "_", os.path.basename(filename))[:120] or "upload"
    path = os.path.join(settings.UPLOAD_DIR, f"{digest[:16]}_{safe}")
    if not os.path.exists(path):
        with open(path, "wb") as f:
            f.write(content)
    return path


def _parse(content: bytes, filename: str) -> Tuple[str, ParseResult]:
    try:
        sheets = read_workbook(content, filename)
    except UnsupportedFile:
        raise
    except Exception as e:  # corrupt or password-protected workbook
        raise UnsupportedFile(f"The file could not be read as a spreadsheet: {e}") from e
    return detect_and_parse(sheets)


def preview(db: Session, content: bytes, filename: str, user_id: Optional[str]) -> ImportBatch:
    if len(content) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise ImportRefused(f"File is larger than {settings.MAX_UPLOAD_MB} MB")
    digest = sha256(content)
    previous = db.scalar(select(ImportBatch).where(ImportBatch.sha256 == digest, ImportBatch.status == "COMMITTED"))
    batch = ImportBatch(filename=filename, sha256=digest, size_bytes=len(content), parser_version=PARSER_VERSION,
                        status="PREVIEWED", uploaded_by=user_id)
    if previous is not None:
        batch.status = "DUPLICATE"
        batch.summary = {"duplicate_of": previous.id, "message": f"This exact file was already imported (batch #{previous.id}, {previous.filename})."}
        batch.source_format = previous.source_format
        db.add(batch)
        db.commit()
        return batch
    batch.stored_path = _store(content, digest, filename)
    try:
        fmt, res = _parse(content, filename)
    except (UnsupportedFile, UnknownFormat) as e:
        batch.status, batch.error = "FAILED", str(e)
        db.add(batch)
        db.commit()
        return batch
    batch.source_format = fmt
    _fill_batch(batch, res)
    batch.summary = {**res.summary, "format_label": FORMATS[fmt], "plan": _plan(db, res), "data_quality": _quality(res)}
    db.add(batch)
    db.flush()
    _save_issues(db, batch, res.issues)
    db.commit()
    return batch


def _fill_batch(batch: ImportBatch, res: ParseResult) -> None:
    dates = sorted({r.prod_date for r in res.records})
    batch.period_start, batch.period_end = (dates[0], dates[-1]) if dates else (None, None)
    batch.records_parsed = len(res.records)
    batch.error_count = sum(1 for i in res.issues if i.severity == "ERROR")
    batch.warning_count = sum(1 for i in res.issues if i.severity == "WARNING")
    batch.reconciliation = [c.as_dict() for c in res.checks]


def _quality(res: ParseResult) -> dict:
    """Data-quality summary: completeness per field and reconciliation outcome."""
    fields = Counter()
    present = Counter()
    for r in res.records:
        for k, v in r.values.items():
            fields[k] += 1
            present[k] += v is not None
    checks = Counter(c.status for c in res.checks)
    return {
        "completeness_pct": {k: round(100 * present[k] / fields[k], 1) for k in sorted(fields)},
        "reconciliation": dict(checks),
        "issues": dict(Counter(f"{i.severity}:{i.code}" for i in res.issues)),
    }


def _existing(db: Session, res: ParseResult) -> Dict[tuple, ShiftProduction]:
    if not res.records:
        return {}
    dates = [r.prod_date for r in res.records]
    looms = {(l.category, l.loom_no): l for l in db.scalars(select(Loom))}
    rows = db.scalars(select(ShiftProduction).where(ShiftProduction.prod_date >= min(dates), ShiftProduction.prod_date <= max(dates)))
    by_id = {l.id: k for k, l in looms.items()}
    out = {}
    for row in rows:
        cat, no = by_id[row.loom_id]
        out[(cat, no, row.prod_date, row.shift, row.source_kind)] = row
    return out


def _diff(existing: Optional[ShiftProduction], rec: Record) -> Tuple[str, Dict[str, tuple]]:
    """'insert', 'update' (with field changes) or 'unchanged'. Empty incoming values never erase stored ones."""
    if existing is None:
        return "insert", {}
    changes = {}
    for k, v in rec.values.items():
        if v is None or k not in VALUE_FIELDS:
            continue
        old = getattr(existing, k)
        if old is None or (isinstance(v, float) and isinstance(old, (int, float)) and abs(old - v) > 1e-9) or (not isinstance(v, float) and old != v):
            changes[k] = (old, v)
    return ("update" if changes else "unchanged"), changes


def _plan(db: Session, res: ParseResult) -> dict:
    existing = _existing(db, res)
    plan = Counter(_diff(existing.get(r.key), r)[0] for r in res.records)
    new_looms = {(r.category, r.loom_no) for r in res.records} - {(l.category, l.loom_no) for l in db.scalars(select(Loom))}
    return {"insert": plan["insert"], "update": plan["update"], "unchanged": plan["unchanged"], "new_looms": len(new_looms)}


def _save_issues(db: Session, batch: ImportBatch, issues) -> None:
    if issues:
        db.execute(insert(ImportIssue), [
            {"batch_id": batch.id, "severity": i.severity, "code": i.code, "message": i.message, "sheet": i.sheet,
             "row": i.row, "column": i.column, "raw_value": i.raw_value} for i in issues
        ])


def _ensure_looms(db: Session, res: ParseResult) -> Dict[Tuple[str, int], Loom]:
    looms = {(l.category, l.loom_no): l for l in db.scalars(select(Loom))}
    for cat, no in sorted({(r.category, r.loom_no) for r in res.records} | {(f.category, f.loom_no) for f in res.loom_facts}):
        if (cat, no) not in looms:
            loom = Loom(code=C.loom_code(cat, no), category=cat, loom_no=no, manufacturer=C.CATEGORIES[cat], attributes={})
            db.add(loom)
            looms[(cat, no)] = loom
    db.flush()
    # Width: the most frequent group the loom appears in (the report regroups looms daily and occasionally mis-files one).
    widths: Dict[tuple, Counter] = {}
    for f in res.loom_facts:
        loom = looms[(f.category, f.loom_no)]
        if f.width_cm:
            widths.setdefault((f.category, f.loom_no), Counter())[f.width_cm] += 1
        if f.attributes:
            loom.attributes = {**(loom.attributes or {}), **f.attributes}
    for key, cnt in widths.items():
        loom = looms[key]
        w = cnt.most_common(1)[0][0]
        if loom.width_cm is None:
            loom.width_cm = w
        if len(cnt) > 1:
            loom.attributes = {**(loom.attributes or {}), "width_groups_seen": {str(k): v for k, v in cnt.items()}}
    return looms


def commit(db: Session, batch: ImportBatch) -> ImportBatch:
    if batch.status != "PREVIEWED":
        raise ImportRefused(f"Batch is {batch.status}; only a previewed batch can be committed")
    if db.scalar(select(ImportBatch.id).where(ImportBatch.sha256 == batch.sha256, ImportBatch.status == "COMMITTED")):
        raise ImportRefused("This exact file has already been committed")
    with open(batch.stored_path, "rb") as f:
        content = f.read()
    fmt, res = _parse(content, batch.filename)
    looms = _ensure_looms(db, res)

    for code, descr in res.styles.items():
        st = db.get(Style, code)
        if st is None:
            db.add(Style(code=code, description=descr))
        elif descr and not st.description:
            st.description = descr
    db.flush()

    raw_ids: Dict[tuple, int] = {}
    if res.raw_rows:
        rows = db.execute(
            insert(RawSourceRow).returning(RawSourceRow.id, RawSourceRow.sheet, RawSourceRow.row),
            [{"batch_id": batch.id, "sheet": s, "row": r, "cells": cells} for (s, r), cells in res.raw_rows.items()],
        )
        raw_ids = {(s, r): i for i, s, r in rows}

    existing = _existing(db, res)
    inserted, updated, unchanged, revised_issues = [], 0, 0, []
    for rec in res.records:
        loom = looms[(rec.category, rec.loom_no)]
        kind, changes = _diff(existing.get(rec.key), rec)
        raw_id = raw_ids.get((rec.sheet, rec.row))
        if kind == "insert":
            row = {k: v for k, v in rec.values.items() if k in VALUE_FIELDS}
            inserted.append({"loom_id": loom.id, "prod_date": rec.prod_date, "shift": rec.shift, "source_kind": rec.source_kind,
                             "data_origin": C.ORIGIN_IMPORTED, "extras": rec.extras, "batch_id": batch.id, "raw_row_id": raw_id, **row})
        elif kind == "update":
            ex = existing[rec.key]
            for k, (old, new) in changes.items():
                setattr(ex, k, new)
                if old is not None and len(revised_issues) < MAX_REVISION_ISSUES:
                    revised_issues.append(("INFO", "REVISED", f"{loom.code} {rec.prod_date} {rec.shift}: {k} {old} -> {new}", rec.sheet, rec.row))
            ex.extras = {**(ex.extras or {}), **rec.extras}
            ex.batch_id, ex.raw_row_id = batch.id, raw_id or ex.raw_row_id
            updated += 1
        else:
            unchanged += 1
    if inserted:
        db.execute(insert(ShiftProduction), inserted)

    # Looms registered in this category that the file does not mention: visible, not silently "zero production".
    cats = {r.category for r in res.records}
    dates = {r.prod_date for r in res.records}
    present = {(r.category, r.loom_no) for r in res.records}
    absent = sorted(l.code for (cat, no), l in looms.items() if cat in cats and (cat, no) not in present)
    if absent and dates:
        res.issue("INFO", "LOOMS_NOT_IN_FILE", f"No rows for {len(absent)} registered loom(s) of this category in this file: {', '.join(absent)}")
    from app.mill.importers.base import Issue
    res.issues.extend(Issue(*t) for t in revised_issues)

    db.query(ImportIssue).filter(ImportIssue.batch_id == batch.id).delete()
    _fill_batch(batch, res)
    _save_issues(db, batch, res.issues)
    batch.source_format = fmt
    batch.records_inserted, batch.records_updated, batch.records_unchanged = len(inserted), updated, unchanged
    batch.summary = {**(batch.summary or {}), **res.summary, "data_quality": _quality(res)}
    batch.status = "COMMITTED"
    batch.committed_at = datetime.now(timezone.utc)
    db.commit()
    logger.info(f"Import batch {batch.id} committed: {len(inserted)} inserted, {updated} updated, {unchanged} unchanged")
    return batch


def import_file(db: Session, content: bytes, filename: str, user_id: Optional[str] = None) -> ImportBatch:
    """Preview and commit in one go (CLI and tests). Raises ImportRefused on a duplicate or unreadable file."""
    batch = preview(db, content, filename, user_id)
    if batch.status == "DUPLICATE":
        raise ImportRefused(batch.summary["message"])
    if batch.status == "FAILED":
        raise ImportRefused(batch.error or "Import failed")
    return commit(db, batch)

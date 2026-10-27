"""GM-to-owner reports, machine connectivity configuration, loom master data and the audit log."""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.v1.mill.common import Page, PageSize, ok, paginate
from app.core.exceptions import NotFoundException, ValidationException
from app.db.session import get_db
from app.mill import audit
from app.mill import constants as C
from app.mill.models import AuditLog, Loom, MachineConnection, OwnerReport
from app.mill.reports.owner import build_snapshot, to_xlsx
from app.mill.telemetry.adapters import requirements
from app.mill.telemetry.collector import collect_once, live_state
from app.models.user import User

router = APIRouter(tags=["Reports, connectivity and settings"])


def utcnow():
    return datetime.now(timezone.utc)


def _report(r: OwnerReport, full: bool = False) -> dict:
    out = {k: getattr(r, k) for k in ("id", "title", "period_start", "period_end", "shift", "status", "generated_at", "published_at",
                                       "acknowledged_at", "owner_comment", "commentary", "decisions_needed", "risks")}
    if full:
        out["snapshot"] = r.snapshot
    return out


class ReportIn(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    period_start: date
    period_end: date
    shift: Optional[str] = None


class ReportPatch(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    commentary: Optional[str] = None
    decisions_needed: Optional[str] = None
    risks: Optional[str] = None


@router.get("/reports")
def reports(page: int = Page, page_size: int = PageSize, db: Session = Depends(get_db)):
    return ok(paginate(db, select(OwnerReport).order_by(OwnerReport.period_end.desc(), OwnerReport.id.desc()), page, page_size, _report))


@router.post("/reports")
def create_report(body: ReportIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.period_start > body.period_end:
        raise ValidationException("The period start must not be after its end")
    if body.shift and body.shift not in C.SHIFTS:
        raise ValidationException("Shift must be A, B or C")
    title = body.title or (f"Weaving report {body.period_start:%d %b %Y}" + (f" to {body.period_end:%d %b %Y}" if body.period_end != body.period_start else "")
                           + (f", shift {body.shift}" if body.shift else ""))
    r = OwnerReport(title=title, period_start=body.period_start, period_end=body.period_end, shift=body.shift, created_by=user.id,
                    snapshot=build_snapshot(db, body.period_start, body.period_end, body.shift))
    db.add(r)
    db.flush()
    audit.record(db, user.id, "REPORT_CREATE", "owner_report", r.id, after={"period": f"{r.period_start}..{r.period_end}", "shift": r.shift})
    db.commit()
    return ok(_report(r, full=True))


@router.get("/reports/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db)):
    r = db.get(OwnerReport, report_id)
    if r is None:
        raise NotFoundException("Report not found")
    return ok(_report(r, full=True))


@router.patch("/reports/{report_id}")
def edit_report(report_id: int, body: ReportPatch, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    r = db.get(OwnerReport, report_id)
    if r is None:
        raise NotFoundException("Report not found")
    if r.status != "DRAFT":
        raise ValidationException("A published report cannot be edited")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(r, k, v)
    db.commit()
    return ok(_report(r, full=True))


@router.post("/reports/{report_id}/refresh")
def refresh_report(report_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    r = db.get(OwnerReport, report_id)
    if r is None:
        raise NotFoundException("Report not found")
    if r.status != "DRAFT":
        raise ValidationException("A published report keeps its numbers; create a new report instead")
    r.snapshot, r.generated_at = build_snapshot(db, r.period_start, r.period_end, r.shift), utcnow()
    db.commit()
    return ok(_report(r, full=True))


@router.post("/reports/{report_id}/publish")
def publish(report_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    r = db.get(OwnerReport, report_id)
    if r is None:
        raise NotFoundException("Report not found")
    if r.status != "DRAFT":
        raise ValidationException("Already published")
    if not (r.commentary or "").strip():
        raise ValidationException("Add the GM's commentary before publishing")
    r.status, r.published_at, r.published_by = "PUBLISHED", utcnow(), user.id
    audit.record(db, user.id, "REPORT_PUBLISH", "owner_report", r.id, {"status": "DRAFT"}, {"status": "PUBLISHED"})
    db.commit()
    return ok(_report(r, full=True))


class AckIn(BaseModel):
    comment: Optional[str] = None


@router.post("/reports/{report_id}/acknowledge")
def acknowledge(report_id: int, body: AckIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    r = db.get(OwnerReport, report_id)
    if r is None:
        raise NotFoundException("Report not found")
    if r.status != "PUBLISHED":
        raise ValidationException("Only a published report can be acknowledged")
    r.status, r.acknowledged_at, r.acknowledged_by, r.owner_comment = "ACKNOWLEDGED", utcnow(), user.id, body.comment
    audit.record(db, user.id, "REPORT_ACKNOWLEDGE", "owner_report", r.id, {"status": "PUBLISHED"}, {"status": "ACKNOWLEDGED"})
    db.commit()
    return ok(_report(r, full=True))


@router.get("/reports/{report_id}/export.xlsx")
def export_xlsx(report_id: int, db: Session = Depends(get_db)):
    r = db.get(OwnerReport, report_id)
    if r is None:
        raise NotFoundException("Report not found")
    return Response(to_xlsx(r), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="weaving-report-{r.id}.xlsx"'})


# ------------------------------------------------------------------ connectivity


class ConnectionIn(BaseModel):
    adapter: str
    host: Optional[str] = Field(None, max_length=120)
    port: Optional[int] = Field(None, ge=1, le=65535)
    credentials_env: Optional[str] = Field(None, max_length=80, pattern=r"^[A-Z_][A-Z0-9_]*$")
    poll_seconds: int = Field(60, ge=10, le=3600)
    enabled: bool = False
    notes: Optional[str] = None


def _conn(loom: Loom, c: Optional[MachineConnection]) -> dict:
    return {"loom": {"id": loom.id, "code": loom.code, "category": loom.category, "manufacturer": loom.manufacturer, "model": loom.model},
            "adapter": c.adapter if c else "NONE", "host": c.host if c else None, "port": c.port if c else None,
            "credentials_env": c.credentials_env if c else None, "poll_seconds": c.poll_seconds if c else None, "enabled": bool(c and c.enabled),
            "state": live_state(c), "last_attempt_at": c.last_attempt_at if c else None, "last_success_at": c.last_success_at if c else None,
            "consecutive_failures": c.consecutive_failures if c else 0, "last_error": c.last_error if c else None, "notes": c.notes if c else None}


@router.get("/connectivity")
def connectivity(db: Session = Depends(get_db)):
    conns = {c.loom_id: c for c in db.scalars(select(MachineConnection))}
    looms = list(db.scalars(select(Loom).order_by(Loom.category, Loom.loom_no)))
    return ok({"connections": [_conn(l, conns.get(l.id)) for l in looms], "adapters": requirements(),
               "policy": ["Read-only: no adapter can start, stop or change a loom.",
                          "Connect through an approved edge gateway or the OEM monitoring server inside the OT network; never expose looms to the internet.",
                          "Credentials live in environment variables on the collector host, never in the database or repository.",
                          "No network scanning or credential guessing."]})


@router.put("/connectivity/{loom_id}")
def set_connection(loom_id: int, body: ConnectionIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    loom = db.get(Loom, loom_id)
    if loom is None:
        raise NotFoundException("Loom not found")
    if body.adapter not in C.ADAPTERS:
        raise ValidationException("Unknown adapter")
    expected = {"TY": "TOYOTA_TMS", "TS": "TSUDAKOMA_TISS"}.get(loom.category)
    if body.adapter not in ("NONE", "SIMULATOR") and body.adapter != expected:
        raise ValidationException(f"{body.adapter} does not fit a {loom.manufacturer} loom")
    c = db.scalar(select(MachineConnection).where(MachineConnection.loom_id == loom_id))
    fields = ("adapter", "host", "port", "credentials_env", "poll_seconds", "enabled", "notes")
    before = audit.snapshot(c, fields) if c else None
    if c is None:
        c = MachineConnection(loom_id=loom_id)
        db.add(c)
    for k, v in body.model_dump().items():
        setattr(c, k, v)
    c.state = "NOT_CONFIGURED" if body.adapter == "NONE" else "CONFIGURED"
    c.next_attempt_at, c.consecutive_failures, c.last_error = None, 0, None
    db.flush()
    audit.record(db, user.id, "CONNECTION_UPDATE", "machine_connection", loom.code, before, audit.snapshot(c, fields))
    db.commit()
    return ok(_conn(loom, c))


@router.post("/connectivity/collect-once")
def collect(db: Session = Depends(get_db)):
    out = collect_once(db)
    db.commit()
    return ok(out)


# ------------------------------------------------------------------ looms and audit


class LoomPatch(BaseModel):
    model: Optional[str] = Field(None, max_length=80)
    width_cm: Optional[int] = Field(None, ge=50, le=600)
    notes: Optional[str] = None
    is_active: Optional[bool] = None


@router.patch("/looms/{loom_id}")
def patch_loom(loom_id: int, body: LoomPatch, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    loom = db.get(Loom, loom_id)
    if loom is None:
        raise NotFoundException("Loom not found")
    data = body.model_dump(exclude_unset=True)
    before = audit.snapshot(loom, tuple(data))
    for k, v in data.items():
        setattr(loom, k, v)
    audit.record(db, user.id, "LOOM_UPDATE", "loom", loom.code, before, audit.snapshot(loom, tuple(data)))
    db.commit()
    return ok({"id": loom.id, "code": loom.code, **{k: getattr(loom, k) for k in ("model", "width_cm", "notes", "is_active")}})


@router.get("/audit")
def audit_log(entity: Optional[str] = None, page: int = Page, page_size: int = PageSize, db: Session = Depends(get_db)):
    q = select(AuditLog)
    if entity:
        q = q.where(AuditLog.entity == entity)
    q = q.order_by(AuditLog.at.desc())
    users = {u.id: u.username for u in db.scalars(select(User))}
    return ok(paginate(db, q, page, page_size, lambda a: {"id": a.id, "at": a.at, "actor": users.get(a.actor_id), "action": a.action,
                                                          "entity": a.entity, "entity_id": a.entity_id, "before": a.before, "after": a.after}))

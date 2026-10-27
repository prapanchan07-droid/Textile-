"""Alerts and their lifecycle, alert rules, notifications and production targets."""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.v1.mill.common import Page, PageSize, ok, paginate
from app.core.exceptions import NotFoundException, ValidationException
from app.db.session import get_db
from app.mill import audit
from app.mill import constants as C
from app.mill.alerts.engine import evaluate_all
from app.mill.models import Alert, AlertEvent, AlertRule, Group, Loom, Notification, Person, ProductionTarget, Task
from app.models.user import User

router = APIRouter(tags=["Alerts"])


def utcnow():
    return datetime.now(timezone.utc)


def _alert(a: Alert, db: Session, events: bool = False) -> dict:
    loom = db.get(Loom, a.loom_id) if a.loom_id else None
    out = {
        "id": a.id, "rule_code": a.rule_code, "title": a.title, "metric": a.metric, "observed": a.observed, "threshold": a.threshold,
        "baseline": a.baseline, "period": a.period_label, "source": a.source, "data_origin": a.data_origin, "severity": a.severity,
        "status": a.status, "occurrences": a.occurrences, "first_seen_at": a.first_seen_at, "last_seen_at": a.last_seen_at,
        "condition_cleared_at": a.condition_cleared_at, "escalation_level": a.escalation_level,
        "loom": {"id": loom.id, "code": loom.code} if loom else None, "group_id": a.group_id,
        "assigned_group_id": a.assigned_group_id, "assigned_person_id": a.assigned_person_id,
        "acknowledged_at": a.acknowledged_at, "resolved_at": a.resolved_at, "resolution_notes": a.resolution_notes,
    }
    if events:
        out["evidence"] = a.evidence
        out["events"] = [{"kind": e.kind, "note": e.note, "at": e.at, "actor_id": e.actor_id}
                         for e in db.scalars(select(AlertEvent).where(AlertEvent.alert_id == a.id).order_by(AlertEvent.at))]
        out["tasks"] = [{"id": t.id, "title": t.title, "status": t.status} for t in db.scalars(select(Task).where(Task.alert_id == a.id))]
    return out


@router.get("/alerts")
def list_alerts(status: Optional[str] = None, severity: Optional[str] = None, loom_id: Optional[int] = None, rule: Optional[str] = None,
                page: int = Page, page_size: int = PageSize, db: Session = Depends(get_db)):
    q = select(Alert)
    if status == "ACTIVE":
        q = q.where(Alert.status != "RESOLVED")
    elif status:
        q = q.where(Alert.status == status.upper())
    if severity:
        q = q.where(Alert.severity == severity.upper())
    if loom_id:
        q = q.where(Alert.loom_id == loom_id)
    if rule:
        q = q.where(Alert.rule_code == rule)
    q = q.order_by(Alert.last_seen_at.desc(), Alert.id.desc())
    return ok(paginate(db, q, page, page_size, lambda a: _alert(a, db)))


@router.get("/alerts/{alert_id}")
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    a = db.get(Alert, alert_id)
    if a is None:
        raise NotFoundException("Alert not found")
    return ok(_alert(a, db, events=True))


class AlertAction(BaseModel):
    note: Optional[str] = Field(None, max_length=4000)
    group_id: Optional[int] = None
    person_id: Optional[int] = None


@router.post("/alerts/{alert_id}/{action}")
def alert_action(alert_id: int, action: str, body: AlertAction, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = db.get(Alert, alert_id)
    if a is None:
        raise NotFoundException("Alert not found")
    before = audit.snapshot(a, ("status", "assigned_group_id", "assigned_person_id", "resolution_notes"))
    now = utcnow()
    if action == "acknowledge":
        if a.status != "OPEN":
            raise ValidationException("Only an open alert can be acknowledged")
        a.status, a.acknowledged_by, a.acknowledged_at = "ACKNOWLEDGED", user.id, now
    elif action == "resolve":
        if a.status == "RESOLVED":
            raise ValidationException("Already resolved")
        if not (body.note or "").strip():
            raise ValidationException("Say what was found or done when resolving")
        a.status, a.resolved_by, a.resolved_at, a.resolution_notes = "RESOLVED", user.id, now, body.note.strip()
    elif action == "reopen":
        if a.status != "RESOLVED":
            raise ValidationException("Only a resolved alert can be reopened")
        a.status, a.resolved_at, a.resolved_by = "OPEN", None, None
    elif action == "assign":
        if body.group_id and db.get(Group, body.group_id) is None or body.person_id and db.get(Person, body.person_id) is None:
            raise ValidationException("Unknown group or person")
        a.assigned_group_id, a.assigned_person_id = body.group_id, body.person_id
    elif action == "comment":
        if not (body.note or "").strip():
            raise ValidationException("Empty comment")
    else:
        raise NotFoundException("Unknown action")
    db.add(AlertEvent(alert_id=a.id, kind={"acknowledge": "ACKNOWLEDGED", "resolve": "RESOLVED", "reopen": "REOPENED", "assign": "ASSIGNED",
                                           "comment": "COMMENT"}[action], note=body.note, actor_id=user.id))
    audit.record(db, user.id, f"ALERT_{action.upper()}", "alert", a.id, before,
                 audit.snapshot(a, ("status", "assigned_group_id", "assigned_person_id", "resolution_notes")))
    db.commit()
    return ok(_alert(a, db, events=True))


@router.post("/alerts/evaluate")
def evaluate(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stats = evaluate_all(db)
    audit.record(db, user.id, "ALERTS_EVALUATE", "alert_rules", None, after=stats)
    db.commit()
    return ok(stats)


# ------------------------------------------------------------------ rules


def _rule(r: AlertRule) -> dict:
    return {k: getattr(r, k) for k in ("id", "code", "name", "description", "metric", "comparator", "threshold", "baseline_days",
                                        "min_baseline_points", "categories", "consecutive", "cooldown_hours", "escalate_after_hours",
                                        "severity", "enabled", "updated_at")}


@router.get("/alert-rules")
def rules(db: Session = Depends(get_db)):
    return ok([_rule(r) for r in db.scalars(select(AlertRule).order_by(AlertRule.id))])


class RulePatch(BaseModel):
    threshold: Optional[float] = None
    consecutive: Optional[int] = Field(None, ge=1, le=20)
    cooldown_hours: Optional[int] = Field(None, ge=0, le=720)
    escalate_after_hours: Optional[int] = Field(None, ge=1, le=720)
    baseline_days: Optional[int] = Field(None, ge=3, le=90)
    min_baseline_points: Optional[int] = Field(None, ge=3, le=200)
    severity: Optional[str] = None
    enabled: Optional[bool] = None
    categories: Optional[str] = None


@router.patch("/alert-rules/{rule_id}")
def patch_rule(rule_id: int, body: RulePatch, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    r = db.get(AlertRule, rule_id)
    if r is None:
        raise NotFoundException("Rule not found")
    data = body.model_dump(exclude_unset=True)
    if "severity" in data and data["severity"] not in C.SEVERITIES:
        raise ValidationException("Unknown severity")
    if data.get("categories"):
        cats = [c.strip().upper() for c in data["categories"].split(",") if c.strip()]
        if any(c not in C.CATEGORIES for c in cats):
            raise ValidationException("Unknown category")
        data["categories"] = ",".join(cats)
    if data.get("enabled") and r.code == "AIR_PER_METER" and not (data.get("threshold") or r.threshold):
        raise ValidationException("Set an air-per-meter limit before enabling this rule")
    before = _rule(r)
    for k, v in data.items():
        setattr(r, k, v)
    db.flush()
    audit.record(db, user.id, "RULE_UPDATE", "alert_rule", r.id, {k: before[k] for k in data}, {k: getattr(r, k) for k in data})
    db.commit()
    return ok(_rule(r))


# ------------------------------------------------------------------ notifications


@router.get("/notifications")
def notifications(unread: bool = False, page: int = Page, page_size: int = PageSize, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = select(Notification).where(Notification.user_id == user.id)
    if unread:
        q = q.where(Notification.read_at.is_(None))
    q = q.order_by(Notification.created_at.desc())
    data = paginate(db, q, page, page_size, lambda n: {"id": n.id, "title": n.title, "body": n.body, "severity": n.severity, "link": n.link,
                                                         "created_at": n.created_at, "read_at": n.read_at, "channel": n.channel,
                                                         "delivery_status": n.delivery_status})
    data["unread"] = db.scalar(select(func.count()).select_from(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None)))
    return ok(data)


@router.post("/notifications/read")
def mark_read(ids: Optional[list[int]] = Body(None), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = update(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None))
    if ids:
        q = q.where(Notification.id.in_(ids))
    db.execute(q.values(read_at=utcnow()))
    db.commit()
    return ok(True)


@router.get("/notification-channels")
def channels():
    from app.mill.alerts.notify import CHANNELS

    return ok([{"channel": k, "configured": v, "note": None if v else "Needs a provider, credentials and a delivery test before it can be enabled."}
               for k, v in CHANNELS.items()])


# ------------------------------------------------------------------ targets


class TargetIn(BaseModel):
    scope: str = Field(pattern="^(MILL|CATEGORY|GROUP|LOOM)$")
    scope_ref: Optional[str] = None
    metric: str = Field(pattern="^(efficiency_pct|meters_per_shift|kilopicks_per_shift)$")
    value: float = Field(gt=0)
    effective_from: date
    effective_to: Optional[date] = None


def _target(t: ProductionTarget) -> dict:
    return {k: getattr(t, k) for k in ("id", "scope", "scope_ref", "metric", "value", "effective_from", "effective_to", "created_at")}


@router.get("/targets")
def targets(db: Session = Depends(get_db)):
    return ok([_target(t) for t in db.scalars(select(ProductionTarget).order_by(ProductionTarget.effective_from.desc()))])


@router.post("/targets")
def add_target(body: TargetIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.scope != "MILL" and not body.scope_ref:
        raise ValidationException("A category, group or loom target needs scope_ref")
    if body.scope == "CATEGORY" and body.scope_ref not in C.CATEGORIES:
        raise ValidationException("Unknown category")
    if body.scope == "LOOM" and not db.scalar(select(Loom.id).where(Loom.code == body.scope_ref)):
        raise ValidationException("Unknown loom code")
    if body.scope == "GROUP" and not (body.scope_ref.isdigit() and db.get(Group, int(body.scope_ref))):
        raise ValidationException("Unknown group id")
    t = ProductionTarget(**body.model_dump(), created_by=user.id)
    db.add(t)
    db.flush()
    audit.record(db, user.id, "TARGET_CREATE", "production_target", t.id, after=body.model_dump(mode="json"))
    db.commit()
    return ok(_target(t))


@router.delete("/targets/{target_id}")
def delete_target(target_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = db.get(ProductionTarget, target_id)
    if t is None:
        raise NotFoundException("Target not found")
    audit.record(db, user.id, "TARGET_DELETE", "production_target", t.id,
                 before=audit.snapshot(t, ("scope", "scope_ref", "metric", "value", "effective_from", "effective_to")))
    db.delete(t)
    db.commit()
    return ok(True)

"""
Alert engine.

  * Production rules are evaluated per loom over its recent loom-shift records (one source per loom-shift, see
    analytics/records.py). A rule opens an alert only after `consecutive` breaching records in a row.
  * One alert per rule and loom at a time (`dedup_key`). A further breach on a newer shift refreshes the open
    alert (occurrences, last value) instead of creating another, so nothing floods.
  * When the latest records no longer breach, the alert is marked "condition cleared" but stays open until a
    person resolves it (no silent auto-resolution).
  * After resolution the same condition re-opens only for a shift newer than the one already handled and once the
    rule's cooldown has passed. Historical breaches therefore never re-trigger.
  * Escalation: an OPEN (unacknowledged) alert older than the rule's `escalate_after_hours` rises one level and
    notifies again, at most once per interval.
  * Notification problems are logged on the notification and never stop evaluation.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.mill import constants as C
from app.mill.alerts.notify import notify_users
from app.mill.analytics import metrics as M
from app.mill.analytics.records import Filters, by, group_of_looms, latest_date, load
from app.mill.analytics.targets import Targets
from app.mill.models import Alert, AlertEvent, AlertRule, Loom, MachineConnection, Task, WorkOrder

PRODUCTION_METRICS = {"efficiency_pct", "efficiency_vs_baseline", "efficiency_robust_z", "warp_stops_cmpx", "weft_stops_cmpx",
                      "rpm_vs_baseline_abs", "meters_vs_target_pct", "air_nm3_per_meter"}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _breach(rule: AlertRule, value: Optional[float]) -> bool:
    if value is None or rule.threshold is None:
        return False
    return value < rule.threshold if rule.comparator == "lt" else value > rule.threshold


def _history(rows: List[dict], i: int, days: int, field: str) -> List[float]:
    r = rows[i]
    return [h[field] for h in rows[:i] if h.get(field) is not None and h["source_kind"] == r["source_kind"]
            and 0 < (r["prod_date"] - h["prod_date"]).days <= days]


def metric_value(rule: AlertRule, rows: List[dict], i: int, targets: Optional[Targets], group_id: Optional[int]) -> Optional[float]:
    r = rows[i]
    m = rule.metric
    if m == "efficiency_pct":
        return r["efficiency_pct"]
    if m in ("warp_stops_cmpx", "weft_stops_cmpx"):
        return M.rate_cmpx([r], m.replace("_cmpx", ""))
    if m in ("efficiency_vs_baseline", "efficiency_robust_z"):
        if r["efficiency_pct"] is None:
            return None
        hist = _history(rows, i, rule.baseline_days, "efficiency_pct")
        if len(hist) < rule.min_baseline_points:
            return None
        return r["efficiency_pct"] - M.median(hist) if m == "efficiency_vs_baseline" else M.robust_z(r["efficiency_pct"], hist)
    if m == "rpm_vs_baseline_abs":
        if r["rpm"] is None:
            return None
        hist = _history(rows, i, rule.baseline_days, "rpm")
        return abs(r["rpm"] - M.median(hist)) if len(hist) >= rule.min_baseline_points else None
    if m == "meters_vs_target_pct":
        if r["meters"] is None or not targets:
            return None
        t = targets.value(r["prod_date"], r["loom_code"], r["category"], group_id)
        return (r["meters"] - t) / t * 100 if t else None
    if m == "air_nm3_per_meter":
        return r["air_nm3"] / r["meters"] if r.get("air_nm3") is not None and r.get("meters") else None
    return None


def _baseline_for(rule: AlertRule, rows: List[dict], i: int) -> Optional[float]:
    if rule.metric in ("efficiency_vs_baseline", "efficiency_robust_z"):
        hist = _history(rows, i, rule.baseline_days, "efficiency_pct")
        return M.median(hist) if hist else None
    if rule.metric == "rpm_vs_baseline_abs":
        hist = _history(rows, i, rule.baseline_days, "rpm")
        return M.median(hist) if hist else None
    return None


def _period(r: dict) -> str:
    return f"{r['prod_date'].isoformat()} {r['shift']}"


def _open_alert(db: Session, rule: AlertRule, key: str, *, title: str, loom_id=None, group_id=None, observed=None, baseline=None,
                period=None, source="SYSTEM", origin=C.ORIGIN_IMPORTED, evidence=None, stats=None) -> Optional[Alert]:
    """Create or refresh the alert for `key`. Returns the alert when something changed."""
    now = utcnow()
    current = db.scalar(select(Alert).where(Alert.dedup_key == key, Alert.status != "RESOLVED"))
    if current is not None:
        if period and current.period_label == period:
            return None  # same breach already recorded
        current.occurrences += 1
        current.last_seen_at = now
        current.observed, current.baseline, current.period_label = observed, baseline, period or current.period_label
        current.evidence = evidence or current.evidence
        current.condition_cleared_at = None
        db.add(AlertEvent(alert_id=current.id, kind="REPEATED", note=f"Breach again {period or ''}: {observed}"))
        if stats is not None:
            stats["refreshed"] += 1
        return current
    last = db.scalar(select(Alert).where(Alert.dedup_key == key, Alert.status == "RESOLVED").order_by(Alert.resolved_at.desc()).limit(1))
    if last is not None:
        if period and last.period_label and period <= last.period_label:
            return None  # the breach was already handled
        if last.resolved_at and now - last.resolved_at < timedelta(hours=rule.cooldown_hours):
            if stats is not None:
                stats["cooldown"] += 1
            return None
    alert = Alert(rule_id=rule.id, rule_code=rule.code, dedup_key=key, loom_id=loom_id, group_id=group_id, assigned_group_id=group_id,
                  title=title, metric=rule.metric, observed=observed, threshold=rule.threshold, baseline=baseline, period_label=period,
                  source=source, data_origin=origin, evidence=evidence or {}, severity=rule.severity, status="OPEN",
                  first_seen_at=now, last_seen_at=now)
    db.add(alert)
    db.flush()
    db.add(AlertEvent(alert_id=alert.id, kind="OPENED", note=f"{rule.name}: observed {observed}, limit {rule.threshold}"))
    if stats is not None:
        stats["opened"] += 1
    notify_users(db, title=title, body=f"{rule.name}. Observed {_fmt(observed)}; limit {_fmt(rule.threshold)}. {period or ''}",
                 severity=rule.severity, alert_id=alert.id, link=f"/alerts?id={alert.id}")
    return alert


def _clear(db: Session, key: str, note: str) -> bool:
    current = db.scalar(select(Alert).where(Alert.dedup_key == key, Alert.status != "RESOLVED"))
    if current is None or current.condition_cleared_at is not None:
        return False
    current.condition_cleared_at = utcnow()
    db.add(AlertEvent(alert_id=current.id, kind="CLEARED", note=note))
    return True


def _fmt(v) -> str:
    return "n/a" if v is None else (f"{v:.2f}" if isinstance(v, float) else str(v))


def evaluate_production(db: Session, stats: Dict[str, int]) -> None:
    rules = [r for r in db.scalars(select(AlertRule).where(AlertRule.enabled.is_(True))) if r.metric in PRODUCTION_METRICS]
    last = latest_date(db)
    if not rules or last is None:
        return
    window = max(r.baseline_days for r in rules) + 7
    rows = load(db, Filters(date_from=last - timedelta(days=window), date_to=last))
    groups = group_of_looms(db, last)
    targets = Targets(db, "meters_per_shift", last - timedelta(days=window), last)
    for (loom_id,), lr in by(rows, "loom_id").items():
        lr.sort(key=lambda r: (r["prod_date"], r["shift"]))
        cat = lr[0]["category"]
        g = groups.get(loom_id)
        for rule in rules:
            if rule.categories and cat not in rule.categories.split(","):
                continue
            n = max(1, rule.consecutive)
            if len(lr) < n:
                continue
            tail = list(range(len(lr) - n, len(lr)))
            vals = [metric_value(rule, lr, i, targets, g.id if g else None) for i in tail]
            key = f"{rule.code}:{lr[0]['loom_code']}"
            stats["evaluated"] += 1
            if all(_breach(rule, v) for v in vals):
                r = lr[-1]
                _open_alert(
                    db, rule, key, title=f"{lr[0]['loom_code']}: {rule.name.lower()}", loom_id=loom_id, group_id=g.id if g else None,
                    observed=round(vals[-1], 3), baseline=_baseline_for(rule, lr, len(lr) - 1), period=_period(r),
                    source=r["source_kind"], origin=r["data_origin"],
                    evidence={"records": [{"period": _period(lr[i]), "value": round(v, 3), "source": lr[i]["source_kind"],
                                           "efficiency_pct": lr[i]["efficiency_pct"], "meters": lr[i]["meters"]} for i, v in zip(tail, vals)],
                              "rule": {"metric": rule.metric, "comparator": rule.comparator, "threshold": rule.threshold,
                                       "consecutive": rule.consecutive, "baseline_days": rule.baseline_days},
                              "definition": M.BY_KEY[rule.metric].formula if rule.metric in M.BY_KEY else rule.description},
                    stats=stats,
                )
            elif not any(_breach(rule, v) for v in vals):
                if _clear(db, key, f"Last {n} record(s) within limits ({_period(lr[-1])})"):
                    stats["cleared"] += 1


def evaluate_missing(db: Session, stats: Dict[str, int]) -> None:
    rule = db.scalar(select(AlertRule).where(AlertRule.code == "NO_RECORD", AlertRule.enabled.is_(True)))
    last = latest_date(db)
    if rule is None or last is None:
        return
    # "Recent" = any record in the last 30 days, so looms missing from a sparse export are still noticed.
    rows = load(db, Filters(date_from=last - timedelta(days=30), date_to=last))
    for (cat,), cr in by(rows, "category").items():
        cat_last = max(r["prod_date"] for r in cr)
        on_last = {r["loom_id"] for r in cr if r["prod_date"] == cat_last}
        for (loom_id,), lr in by(cr, "loom_id").items():
            key = f"NO_RECORD:{lr[0]['loom_code']}"
            if loom_id in on_last:
                _clear(db, key, f"Records again on {cat_last}")
                continue
            seen = max(r["prod_date"] for r in lr)
            _open_alert(db, rule, key, title=f"{lr[0]['loom_code']}: no production recorded on {cat_last}", loom_id=loom_id,
                        observed=float((cat_last - seen).days), period=f"{cat_last.isoformat()}", source="SYSTEM",
                        evidence={"last_record": seen.isoformat(), "latest_date_for_category": cat_last.isoformat()}, stats=stats)


def evaluate_system(db: Session, stats: Dict[str, int], now: Optional[datetime] = None) -> None:
    now = now or utcnow()
    rules = {r.code: r for r in db.scalars(select(AlertRule).where(AlertRule.enabled.is_(True)))}
    if "TELEMETRY_STALE" in rules:
        rule = rules["TELEMETRY_STALE"]
        for conn, loom in db.execute(select(MachineConnection, Loom).join(Loom).where(MachineConnection.enabled.is_(True))):
            key = f"TELEMETRY_STALE:{loom.code}"
            age = (now - conn.last_success_at).total_seconds() if conn.last_success_at else None
            if age is None or age > settings.TELEMETRY_STALE_SECONDS:
                _open_alert(db, rule, key, title=f"{loom.code}: machine data {'never received' if age is None else 'stale'}", loom_id=loom.id,
                            observed=None if age is None else round(age / 60, 1), period=None, source="TELEMETRY",
                            evidence={"adapter": conn.adapter, "state": conn.state, "last_success_at": conn.last_success_at.isoformat() if conn.last_success_at else None,
                                      "last_error": conn.last_error, "stale_after_seconds": settings.TELEMETRY_STALE_SECONDS}, stats=stats)
            else:
                _clear(db, key, "Readings arriving again")
    if "TASK_OVERDUE" in rules:
        rule = rules["TASK_OVERDUE"]
        for t in db.scalars(select(Task).where(Task.status.in_(C.TASK_OPEN), Task.due_at.is_not(None), Task.priority.in_(("HIGH", "CRITICAL")))):
            key = f"TASK_OVERDUE:{t.id}"
            if t.due_at < now:
                _open_alert(db, rule, key, title=f"Task overdue: {t.title}", loom_id=t.loom_id, group_id=t.group_id,
                            observed=round((now - t.due_at).total_seconds() / 3600, 1), period=t.due_at.date().isoformat(),
                            evidence={"task_id": t.id, "due_at": t.due_at.isoformat(), "priority": t.priority, "status": t.status}, stats=stats)
    if "PM_OVERDUE" in rules:
        rule = rules["PM_OVERDUE"]
        today = now.date()
        for w in db.scalars(select(WorkOrder).where(WorkOrder.kind == "PREVENTIVE", WorkOrder.status.in_(("OPEN", "IN_PROGRESS", "ON_HOLD")),
                                                    WorkOrder.due_date.is_not(None), WorkOrder.due_date < today)):
            _open_alert(db, rule, f"PM_OVERDUE:{w.id}", title=f"Preventive work overdue: {w.title}", loom_id=w.loom_id,
                        observed=float((today - w.due_date).days), period=w.due_date.isoformat(),
                        evidence={"work_order_id": w.id, "due_date": w.due_date.isoformat()}, stats=stats)


def escalate(db: Session, now: Optional[datetime] = None) -> int:
    now = now or utcnow()
    count = 0
    for alert, rule in db.execute(select(Alert, AlertRule).join(AlertRule, AlertRule.id == Alert.rule_id).where(Alert.status == "OPEN")):
        if not rule.escalate_after_hours:
            continue
        due_level = int((now - alert.first_seen_at).total_seconds() // (rule.escalate_after_hours * 3600))
        if due_level > alert.escalation_level:
            alert.escalation_level = due_level
            db.add(AlertEvent(alert_id=alert.id, kind="ESCALATED", note=f"Unacknowledged for {rule.escalate_after_hours * due_level} h; level {due_level}"))
            notify_users(db, title=f"Escalated (level {due_level}): {alert.title}", body="Still open and not acknowledged.",
                         severity="CRITICAL" if due_level >= 2 else alert.severity, alert_id=alert.id, link=f"/alerts?id={alert.id}")
            count += 1
    return count


def evaluate_all(db: Session, now: Optional[datetime] = None) -> Dict[str, int]:
    stats = {"evaluated": 0, "opened": 0, "refreshed": 0, "cleared": 0, "cooldown": 0, "escalated": 0}
    steps: List[Callable[[], None]] = [
        lambda: evaluate_production(db, stats),
        lambda: evaluate_missing(db, stats),
        lambda: evaluate_system(db, stats, now),
    ]
    for name, step in zip(("production", "missing", "system"), steps):
        try:
            with db.begin_nested():  # one failing rule family must not undo or stop the others
                step()
        except Exception as e:
            logger.error(f"Alert evaluation step {name} failed: {e}", exc_info=True)
    stats["escalated"] = escalate(db, now)
    db.flush()
    return stats

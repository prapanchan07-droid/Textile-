"""Defaults created at start-up when missing: alert rules (editable afterwards). No production data is ever seeded."""
from __future__ import annotations


from typing import List

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.mill.models import AlertRule, Group

# code, name, metric, comparator, threshold, consecutive, severity, escalate_after_hours, categories, description
DEFAULT_RULES = [
    ("EFF_LOW", "Efficiency below threshold", "efficiency_pct", "lt", 80.0, 2, "WARNING", 24, None,
     "Shift efficiency under the limit for consecutive shifts."),
    ("EFF_CRITICAL", "Efficiency critically low", "efficiency_pct", "lt", 60.0, 1, "CRITICAL", 8, None,
     "One shift under the critical limit: likely an interruption or a loom down for most of the shift."),
    ("EFF_DROP_BASELINE", "Efficiency well below the loom's own normal", "efficiency_vs_baseline", "lt", -8.0, 2, "WARNING", 24, None,
     "Shift efficiency more than 8 points under the loom's median of the previous 14 days (same source), for consecutive shifts."),
    ("EFF_ANOMALY", "Statistically unusual efficiency", "efficiency_robust_z", "lt", -3.5, 1, "INFO", None, None,
     "Robust z-score (median / MAD of the previous 14 days) below -3.5: unusual for this loom, cause unknown."),
    ("WARP_STOP_RATE", "High warp-stop rate", "warp_stops_cmpx", "gt", 6.0, 2, "WARNING", 48, "TY,TS",
     "Warp stops per 100,000 picks above the limit. Not evaluated where warp stops are not recorded (SZ report)."),
    ("WEFT_STOP_RATE", "High weft-stop rate", "weft_stops_cmpx", "gt", 15.0, 2, "WARNING", 48, "TY,TS",
     "Weft (filling) stops per 100,000 picks above the limit."),
    ("RPM_SHIFT", "RPM changed from the loom's normal", "rpm_vs_baseline_abs", "gt", 50.0, 1, "INFO", None, None,
     "RPM differs from the loom's median of the previous 14 days by more than 50. Often a setting or style change: confirm."),
    ("METERS_BELOW_TARGET", "Production below target", "meters_vs_target_pct", "lt", -10.0, 2, "WARNING", 24, None,
     "Shift meters more than 10% under the configured meters-per-shift target. Only evaluated where a target is configured."),
    ("NO_RECORD", "No production recorded", "missing_record", "gt", 0.0, 1, "WARNING", 24, None,
     "A loom with recent records has none for the latest imported day of its category: down, removed, or missing from the report."),
    ("AIR_PER_METER", "High compressed-air use per meter", "air_nm3_per_meter", "gt", 0.0, 1, "WARNING", None, None,
     "Needs measured air consumption. Disabled until air data exists and a limit is set."),
    ("TELEMETRY_STALE", "Machine data stale or disconnected", "telemetry_stale", "gt", 0.0, 1, "WARNING", 4, None,
     "An enabled machine connection has not delivered a reading within the stale window."),
    ("TASK_OVERDUE", "Task past its due time", "task_overdue", "gt", 0.0, 1, "WARNING", 24, None,
     "An open HIGH or CRITICAL task is past its due time."),
    ("PM_OVERDUE", "Preventive maintenance overdue", "maintenance_overdue", "gt", 0.0, 1, "WARNING", 48, None,
     "A preventive work order is past its planned date and not completed."),
]
DISABLED_BY_DEFAULT = {"AIR_PER_METER"}


def ensure_defaults(db: Session) -> None:
    existing = set(db.scalars(select(AlertRule.code)))
    for code, name, metric, cmp_, thr, consec, sev, esc, cats, descr in DEFAULT_RULES:
        if code in existing:
            continue
        db.add(AlertRule(code=code, name=name, metric=metric, comparator=cmp_, threshold=thr, consecutive=consec, severity=sev,
                         escalate_after_hours=esc, categories=cats, description=descr, enabled=code not in DISABLED_BY_DEFAULT))
    db.flush()


def bootstrap_groups(db: Session, count: int = 11) -> List[Group]:
    """Create `count` empty groups (G01..) when none exist. Names, leaders, looms and people are then set by the GM."""
    if db.scalar(select(func.count()).select_from(Group)):
        return []
    groups = [Group(code=f"G{i:02d}", name=f"Group {i}", shift_coverage="A,B,C") for i in range(1, count + 1)]
    db.add_all(groups)
    db.flush()
    return groups




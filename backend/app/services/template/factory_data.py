"""Shared read-side helpers over the data-template tables.

Every dashboard service asks this module for period windows and machine aggregates so
all pages agree on the same numbers.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ingestion import ManpowerRecord
from app.models.template_data import MachineDailyRecord, QualityParameterRecord, BusinessDailyRecord, StockRecord

_DATE_FMT = "%Y-%m-%d"
_SHIFT_ORDER = ["Shift I", "Shift II", "Shift III", "Shift A", "Shift B", "Shift C", "Shift D"]
SHIFT_MINUTES = 480.0
DAY_MINUTES = 1440.0


def _shift_key(shift: Optional[str]) -> int:
    return _SHIFT_ORDER.index(shift) if shift in _SHIFT_ORDER else 99


def _shift_dt(d: str, days: int) -> str:
    return (datetime.strptime(d, _DATE_FMT) + timedelta(days=days)).strftime(_DATE_FMT)


def date_label(d: str) -> str:
    try:
        return datetime.strptime(d, _DATE_FMT).strftime("%b %d")
    except ValueError:
        return d


def status_for_efficiency(eff: float) -> str:
    if eff < 85.0:
        return "CRITICAL"
    if eff < 90.0:
        return "ATTENTION"
    return "NORMAL"


# ---------------------------------------------------------------- windows

@dataclass
class Window:
    start: str
    end: str
    shift: Optional[str] = None
    average_of_history: bool = False  # THREE_MONTH_AVG: scale totals to the current window's day count


def has_template_data(db: Session) -> bool:
    return db.query(MachineDailyRecord.id).first() is not None


def has_manpower_quality_data(db: Session) -> bool:
    return (db.query(ManpowerRecord.id).first() is not None
            or db.query(QualityParameterRecord.id).first() is not None)


def has_business_data(db: Session) -> bool:
    return (db.query(BusinessDailyRecord.id).first() is not None
            or db.query(StockRecord.id).first() is not None)


def latest_date(db: Session) -> Optional[str]:
    return db.query(func.max(MachineDailyRecord.report_date)).scalar()


def available_dates(db: Session) -> List[str]:
    return [r[0] for r in db.query(MachineDailyRecord.report_date).distinct().order_by(MachineDailyRecord.report_date).all()]


def shifts_on(db: Session, d: str) -> List[str]:
    found = {r[0] for r in db.query(MachineDailyRecord.shift).filter(
        MachineDailyRecord.report_date == d, MachineDailyRecord.shift.isnot(None)).distinct().all()}
    return sorted(found, key=_shift_key)


def current_window(db: Session, period: str) -> Optional[Window]:
    latest = latest_date(db)
    if not latest:
        return None
    p = (period or "TODAY").upper()
    if p in ("THIS_WEEK", "WEEK", "LAST_7_DAYS", "SEVEN_DAYS"):
        return Window(_shift_dt(latest, -6), latest)
    if p in ("THIS_MONTH", "MONTH"):
        return Window(_shift_dt(latest, -29), latest)
    if p == "YESTERDAY":
        earlier = [d for d in available_dates(db) if d < latest]
        d = earlier[-1] if earlier else latest
        return Window(d, d)
    if p == "SHIFT":
        shifts = shifts_on(db, latest)
        return Window(latest, latest, shift=shifts[-1] if shifts else None)
    return Window(latest, latest)


def comparison_window(db: Session, cur: Window, comparison: str) -> Optional[Window]:
    c = (comparison or "PREVIOUS_DAY").upper()
    span = (datetime.strptime(cur.end, _DATE_FMT) - datetime.strptime(cur.start, _DATE_FMT)).days + 1
    single_day = span == 1

    if c == "THREE_MONTH_AVG":
        return Window(_shift_dt(cur.start, -90), _shift_dt(cur.start, -1), average_of_history=True)
    if c == "PREVIOUS_WEEK":
        return Window(_shift_dt(cur.start, -7), _shift_dt(cur.end, -7), shift=cur.shift)
    if c == "PREVIOUS_MONTH":
        return Window(_shift_dt(cur.start, -30), _shift_dt(cur.end, -30), shift=cur.shift)

    if c == "PREVIOUS_SHIFT" and cur.shift:
        same_day = shifts_on(db, cur.end)
        if cur.shift in same_day and same_day.index(cur.shift) > 0:
            return Window(cur.end, cur.end, shift=same_day[same_day.index(cur.shift) - 1])
        earlier = [d for d in available_dates(db) if d < cur.start]
        if earlier:
            prev_shifts = shifts_on(db, earlier[-1])
            return Window(earlier[-1], earlier[-1], shift=prev_shifts[-1] if prev_shifts else None)
        return None

    # PREVIOUS_DAY (also the fallback for PREVIOUS_SHIFT on non-shift periods)
    if single_day:
        earlier = [d for d in available_dates(db) if d < cur.start]
        return Window(earlier[-1], earlier[-1], shift=cur.shift) if earlier else None
    return Window(_shift_dt(cur.start, -span), _shift_dt(cur.start, -1), shift=cur.shift)


def query_rows(db: Session, w: Window, unit: Optional[str] = None, section: Optional[str] = None) -> List[MachineDailyRecord]:
    q = db.query(MachineDailyRecord).filter(
        MachineDailyRecord.report_date >= w.start, MachineDailyRecord.report_date <= w.end)
    if w.shift:
        q = q.filter(MachineDailyRecord.shift == w.shift)
    if unit and unit.strip() and unit.strip() != "All Units":
        q = q.filter(MachineDailyRecord.unit == unit.strip())
    rows = q.all()
    if section and section.strip().upper() != "ALL":
        rows = [r for r in rows if (r.section or "").lower() == section.strip().lower()]
    return rows


# ------------------------------------------------------------- aggregates

def _planned_minutes(row: MachineDailyRecord) -> float:
    return SHIFT_MINUTES if row.shift else DAY_MINUTES


@dataclass
class MachineAgg:
    machine_id: str
    machine_type: str
    section: str
    unit: Optional[str]
    actual: float = 0.0
    target: float = 0.0
    downtime_min: float = 0.0
    planned_downtime_min: float = 0.0
    available_min: float = 0.0
    stoppages: int = 0
    power_events: int = 0
    kwh: float = 0.0
    kwh_known: bool = False
    quality_sum: float = 0.0
    quality_n: int = 0
    reasons: Dict[str, float] = field(default_factory=dict)
    issue: Optional[str] = None
    last_maintenance: Optional[str] = None
    next_maintenance: Optional[str] = None
    _issue_date: str = ""

    @property
    def loss(self) -> float:
        return max(0.0, self.target - self.actual)

    @property
    def efficiency(self) -> float:
        return round(self.actual / self.target * 100, 1) if self.target > 0 else 0.0

    @property
    def utilization(self) -> float:
        return round(max(0.0, 100.0 - self.downtime_min / self.available_min * 100), 1) if self.available_min > 0 else 0.0

    @property
    def energy_per_kg(self) -> float:
        return round(self.kwh / self.actual, 3) if self.kwh_known and self.actual > 0 else 0.0

    @property
    def quality(self) -> Optional[float]:
        return round(self.quality_sum / self.quality_n, 1) if self.quality_n else None

    @property
    def main_reason(self) -> Optional[str]:
        return max(self.reasons, key=self.reasons.get) if self.reasons else None

    @property
    def main_issue(self) -> str:
        return self.issue or self.main_reason or "No issue recorded"


@dataclass
class Aggregate:
    machines: Dict[str, MachineAgg]
    n_days: int
    rows: List[MachineDailyRecord]

    @property
    def actual(self) -> float:
        return sum(m.actual for m in self.machines.values())

    @property
    def target(self) -> float:
        return sum(m.target for m in self.machines.values())

    @property
    def loss(self) -> float:
        return max(0.0, self.target - self.actual)

    @property
    def achievement(self) -> float:
        return round(self.actual / self.target * 100, 1) if self.target > 0 else 0.0

    @property
    def avg_efficiency(self) -> float:
        effs = [m.efficiency for m in self.machines.values() if m.target > 0]
        return round(sum(effs) / len(effs), 1) if effs else 0.0

    @property
    def downtime_min(self) -> float:
        return sum(m.downtime_min for m in self.machines.values())

    @property
    def stoppages(self) -> int:
        return sum(m.stoppages for m in self.machines.values())

    @property
    def power_events(self) -> int:
        return sum(m.power_events for m in self.machines.values())

    @property
    def energy_per_kg(self) -> Optional[float]:
        kwh = sum(m.kwh for m in self.machines.values() if m.kwh_known)
        act = sum(m.actual for m in self.machines.values() if m.kwh_known)
        return round(kwh / act, 3) if kwh > 0 and act > 0 else None

    @property
    def quality(self) -> Optional[float]:
        n = sum(m.quality_n for m in self.machines.values())
        return round(sum(m.quality_sum for m in self.machines.values()) / n, 1) if n else None

    def ranked_by_loss(self) -> List[MachineAgg]:
        return sorted(self.machines.values(), key=lambda m: (m.loss, -m.efficiency), reverse=True)


def aggregate(rows: List[MachineDailyRecord]) -> Aggregate:
    machines: Dict[str, MachineAgg] = {}
    for r in sorted(rows, key=lambda x: x.report_date):
        m = machines.get(r.machine_id)
        if m is None:
            m = machines[r.machine_id] = MachineAgg(
                machine_id=r.machine_id, machine_type=r.machine_type, section=r.section or r.machine_type, unit=r.unit)
        m.actual += r.actual_kg
        m.target += r.target_kg
        m.downtime_min += r.downtime_min
        if r.is_planned_downtime:
            m.planned_downtime_min += r.downtime_min
        m.available_min += _planned_minutes(r)
        m.stoppages += r.stoppage_count
        m.power_events += r.power_events
        if r.energy_kwh is not None:
            m.kwh += r.energy_kwh
            m.kwh_known = True
        if r.quality_rating_pct is not None:
            m.quality_sum += r.quality_rating_pct
            m.quality_n += 1
        if r.downtime_reason and r.downtime_min > 0:
            m.reasons[r.downtime_reason] = m.reasons.get(r.downtime_reason, 0.0) + r.downtime_min
        if r.main_issue and r.report_date >= m._issue_date:
            m.issue, m._issue_date = r.main_issue, r.report_date
        if r.last_maintenance:
            m.last_maintenance = r.last_maintenance
        if r.next_maintenance:
            m.next_maintenance = r.next_maintenance
    return Aggregate(machines=machines, n_days=len({r.report_date for r in rows}), rows=rows)


def aggregate_window(db: Session, w: Optional[Window], unit: Optional[str] = None,
                     section: Optional[str] = None, scale_days: int = 1) -> Optional[Aggregate]:
    """Aggregate a window; returns None if the window has no rows. For a 3-month-average window,
    volume totals are scaled to `scale_days` so they are comparable with the current window."""
    if w is None:
        return None
    rows = query_rows(db, w, unit, section)
    if not rows:
        return None
    agg = aggregate(rows)
    if w.average_of_history and agg.n_days > 0:
        factor = scale_days / agg.n_days
        for m in agg.machines.values():
            for attr in ("actual", "target", "downtime_min", "planned_downtime_min", "kwh", "available_min"):
                setattr(m, attr, getattr(m, attr) * factor)
            m.stoppages = round(m.stoppages * factor)
            m.power_events = round(m.power_events * factor)
    return agg


def daily_series(db: Session, last_n: int = 7, machine_id: Optional[str] = None,
                 unit: Optional[str] = None) -> List[tuple]:
    """[(date, Aggregate)] for the last `last_n` available dates (oldest first)."""
    dates = available_dates(db)[-last_n:]
    out = []
    for d in dates:
        rows = query_rows(db, Window(d, d), unit)
        if machine_id:
            rows = [r for r in rows if r.machine_id == machine_id]
        if rows:
            out.append((d, aggregate(rows)))
    return out


# ------------------------------------------------------------ loss analysis

@dataclass
class LossCategory:
    category: str
    kg: float
    percentage: float
    minutes: float
    machine_ids: Set[str]
    events: int


def loss_breakdown(agg: Aggregate) -> List[LossCategory]:
    """Split production loss into downtime reasons (time lost x planned rate) and efficiency loss (the rest)."""
    raw: Dict[str, dict] = {}

    def bucket(name: str) -> dict:
        return raw.setdefault(name, {"kg": 0.0, "min": 0.0, "machines": set(), "events": 0})

    for r in agg.rows:
        gap = max(0.0, r.target_kg - r.actual_kg)
        if gap <= 0:
            continue
        planned = _planned_minutes(r)
        downtime_kg = min(gap, r.target_kg * r.downtime_min / planned) if r.downtime_min > 0 else 0.0
        if downtime_kg > 0:
            b = bucket(r.downtime_reason or "Machine Downtime")
            b["kg"] += downtime_kg
            b["min"] += r.downtime_min
            b["machines"].add(r.machine_id)
            b["events"] += r.power_events
        if gap - downtime_kg > 0:
            b = bucket("Efficiency Loss")
            b["kg"] += gap - downtime_kg
            b["machines"].add(r.machine_id)

    total_raw = sum(b["kg"] for b in raw.values())
    factory_loss = agg.loss
    result = []
    for name, b in sorted(raw.items(), key=lambda kv: kv[1]["kg"], reverse=True):
        share = b["kg"] / total_raw if total_raw > 0 else 0.0
        result.append(LossCategory(
            category=name, kg=round(share * factory_loss, 1), percentage=round(share * 100, 1),
            minutes=b["min"], machine_ids=b["machines"], events=b["events"]))
    return result

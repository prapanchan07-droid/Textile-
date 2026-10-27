"""
Loading the loom-shift rows every analytic starts from.

One row per loom, date and shift. When both sources exist for the same loom-shift, the mill report is used by
default (it is the mill's own book of record; `source=` overrides). Every row carries its `source_kind` so pages
can say where a number came from, and comparisons that are only valid within one source can filter on it.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional, Sequence

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.mill import constants as C
from app.mill.models import Group, GroupLoomAssignment, Loom, ShiftProduction

FIELDS = ("rpm", "efficiency_pct", "loom_efficiency_pct", "kilopicks", "meters", "warp_stops", "weft_stops", "other_stops",
          "total_stops", "run_min", "stop_min", "warp_stop_min", "weft_stop_min", "air_nm3", "style_code", "operator_name")


@dataclass
class Filters:
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    shifts: Sequence[str] = ()
    categories: Sequence[str] = ()
    loom_ids: Sequence[int] = ()
    group_id: Optional[int] = None
    style: Optional[str] = None
    source: str = "auto"  # auto | MILL_REPORT | MACHINE_EXPORT

    def describe(self) -> dict:
        return {k: (v.isoformat() if isinstance(v, date) else (list(v) if isinstance(v, (list, tuple)) else v))
                for k, v in self.__dict__.items() if v not in (None, (), [], "")}


def latest_date(db: Session) -> Optional[date]:
    return db.scalar(select(ShiftProduction.prod_date).order_by(ShiftProduction.prod_date.desc()).limit(1))


def resolve_period(db: Session, period: str = "latest", date_from: Optional[date] = None, date_to: Optional[date] = None) -> Dict:
    """Periods are anchored on the latest date that has data, because imported reports lag the calendar."""
    last = latest_date(db)
    if period == "custom" and date_from and date_to:
        return {"key": "custom", "date_from": date_from, "date_to": date_to, "anchor": last}
    if last is None:
        return {"key": period, "date_from": None, "date_to": None, "anchor": None}
    if period == "7d":
        return {"key": "7d", "date_from": last - timedelta(days=6), "date_to": last, "anchor": last}
    if period == "30d":
        return {"key": "30d", "date_from": last - timedelta(days=29), "date_to": last, "anchor": last}
    if period == "month":
        return {"key": "month", "date_from": last.replace(day=1), "date_to": last, "anchor": last}
    return {"key": "latest", "date_from": last, "date_to": last, "anchor": last}


def group_of_looms(db: Session, on: date) -> Dict[int, Group]:
    q = (select(GroupLoomAssignment, Group).join(Group, Group.id == GroupLoomAssignment.group_id)
         .where(GroupLoomAssignment.valid_from <= on, or_(GroupLoomAssignment.valid_to.is_(None), GroupLoomAssignment.valid_to > on)))
    return {a.loom_id: g for a, g in db.execute(q)}


def load(db: Session, f: Filters) -> List[dict]:
    q = select(ShiftProduction, Loom).join(Loom, Loom.id == ShiftProduction.loom_id).where(Loom.is_active.is_(True))
    if f.date_from:
        q = q.where(ShiftProduction.prod_date >= f.date_from)
    if f.date_to:
        q = q.where(ShiftProduction.prod_date <= f.date_to)
    if f.shifts:
        q = q.where(ShiftProduction.shift.in_(list(f.shifts)))
    if f.categories:
        q = q.where(Loom.category.in_(list(f.categories)))
    if f.loom_ids:
        q = q.where(Loom.id.in_(list(f.loom_ids)))
    if f.style:
        q = q.where(ShiftProduction.style_code == f.style)
    if f.source in C.SOURCE_KINDS:
        q = q.where(ShiftProduction.source_kind == f.source)
    if f.group_id is not None:
        # Membership is by date: a loom counts for the group only while it was assigned to it.
        q = q.join(GroupLoomAssignment, and_(
            GroupLoomAssignment.loom_id == Loom.id, GroupLoomAssignment.group_id == f.group_id,
            GroupLoomAssignment.valid_from <= ShiftProduction.prod_date,
            or_(GroupLoomAssignment.valid_to.is_(None), GroupLoomAssignment.valid_to > ShiftProduction.prod_date),
        ))
    chosen: Dict[tuple, dict] = {}
    for sp, loom in db.execute(q):
        key = (sp.loom_id, sp.prod_date, sp.shift)
        row = {"id": sp.id, "loom_id": loom.id, "loom_code": loom.code, "category": loom.category, "width_cm": loom.width_cm,
               "prod_date": sp.prod_date, "shift": sp.shift, "source_kind": sp.source_kind, "data_origin": sp.data_origin,
               "batch_id": sp.batch_id, **{k: getattr(sp, k) for k in FIELDS}}
        prev = chosen.get(key)
        if prev is None or (f.source == "auto" and sp.source_kind == C.SOURCE_MILL_REPORT and prev["source_kind"] != C.SOURCE_MILL_REPORT):
            chosen[key] = row
    return sorted(chosen.values(), key=lambda r: (r["prod_date"], r["shift"], r["loom_code"]))


def by(rows: List[dict], *keys: str) -> Dict[tuple, List[dict]]:
    out: Dict[tuple, List[dict]] = {}
    for r in rows:
        out.setdefault(tuple(r[k] for k in keys), []).append(r)
    return out


def dominant_style(rows: List[dict]) -> Optional[str]:
    counts: Dict[str, int] = {}
    for r in rows:
        if r.get("style_code"):
            counts[r["style_code"]] = counts.get(r["style_code"], 0) + 1
    return max(counts, key=counts.get) if counts else None


def cohort_key(loom_rows: List[dict]) -> tuple:
    """Peers: same category (manufacturer), reed width group and dominant style, from the same source."""
    r0 = loom_rows[0]
    return (r0["category"], r0["width_cm"], dominant_style(loom_rows), r0["source_kind"])


__all__ = ["Filters", "load", "by", "resolve_period", "latest_date", "cohort_key", "dominant_style", "group_of_looms", "FIELDS"]

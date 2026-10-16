"""
Loads aggregated rows from the fact tables. One grouped query per fact table per window; everything
else (rollups by loom, style, beam, shift, day...) happens in Python on those small result sets, so a
dashboard costs a handful of queries and never one per loom.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import Float, and_, case, cast, func, select
from sqlalchemy.orm import Session

from app.weaving import models as m
from app.weaving.analytics.calendar import ReportWindow
from app.weaving.analytics.definitions import PICKS_PER_METRE_PER_PPI


def _f(v) -> float:
    return float(v) if v is not None else 0.0


# ---------------------------------------------------------------------------- reference data

@dataclass
class Refs:
    looms: Dict[int, m.WvLoom]
    styles: Dict[int, m.WvStyle]
    beams: Dict[int, m.WvBeam]
    shifts: Dict[int, m.WvShift]
    reasons: Dict[int, m.WvStopReason]
    defect_types: Dict[int, m.WvDefectType]
    operators: Dict[int, m.WvOperator]

    def loom_code(self, i: int) -> str:
        return self.looms[i].loom_code if i in self.looms else f"loom#{i}"

    def style_code(self, i: Optional[int]) -> str:
        return self.styles[i].style_code if i in self.styles else "unassigned"

    def beam_no(self, i: Optional[int]) -> str:
        return self.beams[i].beam_no if i in self.beams else "none"

    def shift_name(self, i: int) -> str:
        return self.shifts[i].name if i in self.shifts else f"shift#{i}"

    def contribution_per_m(self, style_id: Optional[int]) -> float:
        s = self.styles.get(style_id) if style_id is not None else None
        return max(0.0, _f(s.rate_per_m) - _f(s.variable_cost_per_m)) if s else 0.0


def load_refs(db: Session) -> Refs:
    def by_id(model):
        return {r.id: r for r in db.scalars(select(model))}

    return Refs(
        looms=by_id(m.WvLoom), styles=by_id(m.WvStyle), beams=by_id(m.WvBeam), shifts=by_id(m.WvShift),
        reasons=by_id(m.WvStopReason), defect_types=by_id(m.WvDefectType), operators=by_id(m.WvOperator),
    )


# ---------------------------------------------------------------------------- production

@dataclass
class ProdRow:
    loom_id: int
    shift_date: object
    shift_id: int
    style_id: Optional[int]
    beam_id: Optional[int]
    weaver_id: Optional[int]
    scheduled_s: float
    running_s: float
    measured_s: float  # scheduled seconds that have a pick count
    measured_running_s: float  # running seconds in those readings
    picks: float
    capacity_picks: float
    meters: float
    target_meters: float
    readings: int
    no_picks: int
    partial: int
    demo: int  # readings with data_origin DEMO


def load_production(db: Session, start_date, end_date, loom_ids: Optional[List[int]] = None) -> List[ProdRow]:
    R, L, S = m.WvLoomReading, m.WvLoom, m.WvStyle
    has_picks = R.picks.isnot(None)
    # Everything numeric is cast to double precision on purpose: left alone, SQLAlchemy gives the arithmetic the
    # NUMERIC(6,1)/(5,2) type of the columns involved and digits are lost (a test caught this).
    capacity = cast(L.rated_rpm * R.duration_seconds, Float) / 60.0  # picks the loom could insert in the interval
    ppm = cast(S.ppi, Float) * PICKS_PER_METRE_PER_PPI  # picks per metre
    q = (
        select(
            R.loom_id, R.shift_date, R.shift_id, R.style_id, R.beam_id, R.weaver_id,
            func.sum(R.duration_seconds), func.sum(R.running_seconds),
            func.sum(case((has_picks, R.duration_seconds), else_=0)),
            func.sum(case((has_picks, R.running_seconds), else_=0)),
            func.coalesce(func.sum(R.picks), 0),
            func.coalesce(func.sum(case((has_picks, capacity), else_=0.0)), 0.0),
            func.coalesce(func.sum(case((and_(has_picks, S.id.isnot(None)), cast(R.picks, Float) / ppm), else_=0.0)), 0.0),
            func.coalesce(func.sum(case((and_(has_picks, S.id.isnot(None)), cast(S.target_efficiency_pct, Float) / 100.0 * capacity / ppm), else_=0.0)), 0.0),
            func.count(), func.sum(case((has_picks, 0), else_=1)),
            func.sum(case((R.quality_flag == "PARTIAL", 1), else_=0)),
            func.sum(case((R.data_origin == "DEMO", 1), else_=0)),
        )
        .join(L, L.id == R.loom_id)
        .outerjoin(S, S.id == R.style_id)
        .where(R.shift_date.between(start_date, end_date))
        .group_by(R.loom_id, R.shift_date, R.shift_id, R.style_id, R.beam_id, R.weaver_id)
    )
    if loom_ids is not None:
        q = q.where(R.loom_id.in_(loom_ids))
    return [
        ProdRow(r[0], r[1], r[2], r[3], r[4], r[5], _f(r[6]), _f(r[7]), _f(r[8]), _f(r[9]), _f(r[10]), _f(r[11]), _f(r[12]), _f(r[13]), int(r[14]), int(r[15]), int(r[16]), int(r[17]))
        for r in db.execute(q)
    ]


# ---------------------------------------------------------------------------- stoppages

@dataclass
class StopRow:
    loom_id: int
    reason_id: int
    shift_id: int
    shift_date: object
    style_id: Optional[int]
    beam_id: Optional[int]
    weaver_id: Optional[int]
    is_planned: bool
    counts_toward_rate: bool
    events: int  # stops that started inside the window
    eligible_events: int  # ... that count toward the stop rate
    downtime_s: float  # clipped to the window
    closed_events: int  # unplanned stops that started in the window and have ended
    closed_duration_s: float
    open_events: int
    demo: int


def load_stops(db: Session, window: ReportWindow, now: datetime, loom_ids: Optional[List[int]] = None) -> List[StopRow]:
    E, RS = m.WvStopEvent, m.WvStopReason
    ws, we = window.start_at, window.end_at
    end_or_now = func.coalesce(E.ended_at, now)
    overlap = func.extract("epoch", func.least(end_or_now, we) - func.greatest(E.started_at, ws))
    started_in = E.started_at >= ws
    q = (
        select(
            E.loom_id, E.reason_id, E.shift_id, E.shift_date, E.style_id, E.beam_id, E.weaver_id, RS.is_planned, RS.counts_toward_stop_rate,
            func.sum(case((started_in, 1), else_=0)),
            func.sum(case((and_(started_in, RS.counts_toward_stop_rate), 1), else_=0)),
            func.coalesce(func.sum(overlap), 0),
            func.sum(case((and_(started_in, E.ended_at.isnot(None), RS.is_planned.is_(False)), 1), else_=0)),
            func.coalesce(func.sum(case((and_(started_in, E.ended_at.isnot(None), RS.is_planned.is_(False)), func.extract("epoch", E.ended_at - E.started_at)), else_=0)), 0),
            func.sum(case((E.ended_at.is_(None), 1), else_=0)),
            func.sum(case((E.data_origin == "DEMO", 1), else_=0)),
        )
        .join(RS, RS.id == E.reason_id)
        .where(E.started_at < we, end_or_now > ws)
        .group_by(E.loom_id, E.reason_id, E.shift_id, E.shift_date, E.style_id, E.beam_id, E.weaver_id, RS.is_planned, RS.counts_toward_stop_rate)
    )
    if loom_ids is not None:
        q = q.where(E.loom_id.in_(loom_ids))
    return [
        StopRow(r[0], r[1], r[2], r[3], r[4], r[5], r[6], bool(r[7]), bool(r[8]), int(r[9]), int(r[10]), _f(r[11]), int(r[12]), _f(r[13]), int(r[14]), int(r[15]))
        for r in db.execute(q)
    ]


# ---------------------------------------------------------------------------- quality

@dataclass
class InspRow:
    loom_id: int
    style_id: int
    beam_id: Optional[int]
    shift_id: int
    shift_date: object
    rolls: int
    length_m: float
    grade_a_m: float
    grade_b_m: float
    grade_c_m: float
    reject_m: float
    demo: int


@dataclass
class DefectRow:
    loom_id: int
    style_id: int
    beam_id: Optional[int]
    shift_id: int
    shift_date: object
    defect_type_id: int
    severity: str
    defects: int
    points: int


def load_inspections(db: Session, start_date, end_date) -> List[InspRow]:
    I = m.WvInspection

    def graded(g):
        return func.coalesce(func.sum(case((I.grade == g, I.length_m), else_=0)), 0)

    q = (
        select(I.loom_id, I.style_id, I.beam_id, I.shift_id, I.shift_date, func.count(), func.sum(I.length_m),
               graded("A"), graded("B"), graded("C"), graded("REJECT"), func.sum(case((I.data_origin == "DEMO", 1), else_=0)))
        .where(I.shift_date.between(start_date, end_date))
        .group_by(I.loom_id, I.style_id, I.beam_id, I.shift_id, I.shift_date)
    )
    return [InspRow(r[0], r[1], r[2], r[3], r[4], int(r[5]), _f(r[6]), _f(r[7]), _f(r[8]), _f(r[9]), _f(r[10]), int(r[11])) for r in db.execute(q)]


def load_defects(db: Session, start_date, end_date) -> List[DefectRow]:
    I, D = m.WvInspection, m.WvDefectObservation
    q = (
        select(I.loom_id, I.style_id, I.beam_id, I.shift_id, I.shift_date, D.defect_type_id, D.severity,
               func.sum(D.defect_count), func.sum(D.points * D.defect_count))
        .join(I, I.id == D.inspection_id)
        .where(I.shift_date.between(start_date, end_date))
        .group_by(I.loom_id, I.style_id, I.beam_id, I.shift_id, I.shift_date, D.defect_type_id, D.severity)
    )
    return [DefectRow(r[0], r[1], r[2], r[3], r[4], r[5], r[6], int(r[7]), int(r[8])) for r in db.execute(q)]


# ---------------------------------------------------------------------------- machine sensors

@dataclass
class SensorDay:
    loom_id: int
    shift_date: object
    shift_id: int
    readings: int  # hourly readings in the group
    with_sensors: int  # of those, readings that have sensor values
    vibration: Optional[float]  # mean over hours when the loom was mostly running
    temperature: Optional[float]
    pressure: Optional[float]
    power_kw: Optional[float]
    kwh: float  # electrical energy over all readings that have a power value


def load_sensor_days(db: Session, start_date, end_date) -> List[SensorDay]:
    R = m.WvLoomReading
    running = R.running_seconds >= 1800  # averages are taken while the loom is mostly running, so idle hours do not skew them
    has = R.power_kw.isnot(None)

    def avg(col):
        return func.avg(case((and_(running, col.isnot(None)), cast(col, Float)), else_=None))

    q = (
        select(R.loom_id, R.shift_date, R.shift_id, func.count(), func.sum(case((has, 1), else_=0)), avg(R.vibration_mm_s), avg(R.motor_temp_c), avg(R.air_pressure_bar), avg(R.power_kw),
               func.coalesce(func.sum(case((has, cast(R.power_kw, Float) * R.duration_seconds / 3600.0), else_=0.0)), 0.0))
        .where(R.shift_date.between(start_date, end_date))
        .group_by(R.loom_id, R.shift_date, R.shift_id)
    )
    return [SensorDay(r[0], r[1], r[2], int(r[3]), int(r[4]), None if r[5] is None else float(r[5]), None if r[6] is None else float(r[6]),
                      None if r[7] is None else float(r[7]), None if r[8] is None else float(r[8]), float(r[9])) for r in db.execute(q)]


# ---------------------------------------------------------------------------- hourly progress of one production day

@dataclass
class HourRow:
    start: datetime
    shift_id: int
    meters: float
    target_m: float
    running_s: float
    scheduled_s: float
    stopped_looms: int


def load_hourly(db: Session, shift_date) -> List[HourRow]:
    R, L, S = m.WvLoomReading, m.WvLoom, m.WvStyle
    capacity = cast(L.rated_rpm * R.duration_seconds, Float) / 60.0
    ppm = cast(S.ppi, Float) * PICKS_PER_METRE_PER_PPI
    has = and_(R.picks.isnot(None), S.id.isnot(None))
    q = (
        select(R.reading_start, R.shift_id, func.coalesce(func.sum(case((has, cast(R.picks, Float) / ppm), else_=0.0)), 0.0),
               func.coalesce(func.sum(case((has, cast(S.target_efficiency_pct, Float) / 100.0 * capacity / ppm), else_=0.0)), 0.0),
               func.sum(R.running_seconds), func.sum(R.duration_seconds), func.sum(case((R.running_seconds < R.duration_seconds / 2, 1), else_=0)))
        .join(L, L.id == R.loom_id).outerjoin(S, S.id == R.style_id)
        .where(R.shift_date == shift_date)
        .group_by(R.reading_start, R.shift_id).order_by(R.reading_start)
    )
    return [HourRow(r[0], r[1], float(r[2]), float(r[3]), float(r[4] or 0), float(r[5] or 0), int(r[6] or 0)) for r in db.execute(q)]


# ---------------------------------------------------------------------------- when do stops happen

def load_stop_heat(db: Session, start_at: datetime, end_at: datetime, tz: str, unplanned_only: bool = True) -> List[tuple]:
    """(weekday 0=Monday, hour of day in mill time, stops, downtime seconds) for stops that started in the window."""
    E, RS = m.WvStopEvent, m.WvStopReason
    local = func.timezone(tz, E.started_at)
    dur = func.extract("epoch", func.coalesce(E.ended_at, end_at) - E.started_at)
    dow, hour = func.extract("isodow", local), func.extract("hour", local)
    q = (
        select(dow, hour, func.count(), func.coalesce(func.sum(dur), 0))
        .join(RS, RS.id == E.reason_id)
        .where(E.started_at >= start_at, E.started_at < end_at)
        .group_by(dow, hour)
    )
    if unplanned_only:
        q = q.where(RS.is_planned.is_(False))
    return [(int(r[0]) - 1, int(r[1]), int(r[2]), float(r[3])) for r in db.execute(q)]

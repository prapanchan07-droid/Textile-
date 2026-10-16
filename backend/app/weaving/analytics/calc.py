"""
Metric formulas, as pure functions over the rows loaded by facts.py (see definitions.py for the
written definitions). No database access here, so every formula is unit-tested against known fixtures.
Undefined results (division by zero, no data) are None, never 0, so "no data" is not shown as "bad".
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from app.weaving.analytics.facts import DefectRow, InspRow, ProdRow, Refs, StopRow


def _pct(num: float, den: float) -> Optional[float]:
    return num / den * 100.0 if den > 0 else None


# ---------------------------------------------------------------------------- production

@dataclass
class ProdAgg:
    scheduled_s: float = 0.0
    running_s: float = 0.0
    measured_s: float = 0.0
    measured_running_s: float = 0.0
    picks: float = 0.0
    capacity_picks: float = 0.0
    meters: float = 0.0
    target_meters: float = 0.0
    readings: int = 0
    no_picks: int = 0
    partial: int = 0
    demo: int = 0

    def add(self, r: ProdRow) -> "ProdAgg":
        self.scheduled_s += r.scheduled_s
        self.running_s += r.running_s
        self.measured_s += r.measured_s
        self.measured_running_s += r.measured_running_s
        self.picks += r.picks
        self.capacity_picks += r.capacity_picks
        self.meters += r.meters
        self.target_meters += r.target_meters
        self.readings += r.readings
        self.no_picks += r.no_picks
        self.partial += r.partial
        self.demo += r.demo
        return self

    @property
    def scheduled_h(self) -> float:
        return self.scheduled_s / 3600.0

    @property
    def running_h(self) -> float:
        return self.running_s / 3600.0

    @property
    def utilization_pct(self) -> Optional[float]:
        return _pct(self.running_s, self.scheduled_s)

    @property
    def efficiency_pct(self) -> Optional[float]:
        return _pct(self.picks, self.capacity_picks)

    @property
    def achievement_pct(self) -> Optional[float]:
        return _pct(self.meters, self.target_meters)

    @property
    def run_rate_m_per_min(self) -> Optional[float]:
        """Observed output while running, from readings that have a pick count."""
        return self.meters / (self.measured_running_s / 60.0) if self.measured_running_s > 0 and self.meters > 0 else None

    @property
    def meters_per_scheduled_hour(self) -> Optional[float]:
        return self.meters / (self.measured_s / 3600.0) if self.measured_s > 0 else None


def roll_production(rows: Iterable[ProdRow], key: Callable[[ProdRow], object]) -> Dict[object, ProdAgg]:
    out: Dict[object, ProdAgg] = defaultdict(ProdAgg)
    for r in rows:
        out[key(r)].add(r)
    return dict(out)


def total_production(rows: Iterable[ProdRow]) -> ProdAgg:
    agg = ProdAgg()
    for r in rows:
        agg.add(r)
    return agg


# ---------------------------------------------------------------------------- stoppages

@dataclass
class StopAgg:
    events: int = 0
    eligible_events: int = 0
    downtime_s: float = 0.0
    planned_downtime_s: float = 0.0
    closed_events: int = 0
    closed_duration_s: float = 0.0
    open_events: int = 0
    demo: int = 0

    def add(self, r: StopRow) -> "StopAgg":
        self.events += r.events
        self.eligible_events += r.eligible_events
        self.downtime_s += r.downtime_s
        if r.is_planned:
            self.planned_downtime_s += r.downtime_s
        self.closed_events += r.closed_events
        self.closed_duration_s += r.closed_duration_s
        self.open_events += r.open_events
        self.demo += r.demo
        return self

    @property
    def downtime_min(self) -> float:
        return self.downtime_s / 60.0

    @property
    def unplanned_downtime_min(self) -> float:
        return (self.downtime_s - self.planned_downtime_s) / 60.0

    @property
    def avg_duration_min(self) -> Optional[float]:
        return self.closed_duration_s / self.closed_events / 60.0 if self.closed_events else None

    def per_100k_picks(self, picks: float) -> Optional[float]:
        return self.eligible_events / picks * 100_000.0 if picks > 0 else None


def roll_stops(rows: Iterable[StopRow], key: Callable[[StopRow], object]) -> Dict[object, StopAgg]:
    out: Dict[object, StopAgg] = defaultdict(StopAgg)
    for r in rows:
        out[key(r)].add(r)
    return dict(out)


def total_stops(rows: Iterable[StopRow]) -> StopAgg:
    agg = StopAgg()
    for r in rows:
        agg.add(r)
    return agg


# ---------------------------------------------------------------------------- quality

@dataclass
class QualAgg:
    rolls: int = 0
    length_m: float = 0.0
    grade_a_m: float = 0.0
    grade_b_m: float = 0.0
    grade_c_m: float = 0.0
    reject_m: float = 0.0
    defects: int = 0
    points: int = 0
    demo: int = 0

    @property
    def defects_per_100m(self) -> Optional[float]:
        return self.defects / self.length_m * 100.0 if self.length_m > 0 else None

    @property
    def points_per_100m(self) -> Optional[float]:
        return self.points / self.length_m * 100.0 if self.length_m > 0 else None

    @property
    def grade_a_pct(self) -> Optional[float]:
        return _pct(self.grade_a_m, self.length_m)

    @property
    def grade_b_pct(self) -> Optional[float]:
        return _pct(self.grade_b_m, self.length_m)

    @property
    def grade_c_pct(self) -> Optional[float]:
        return _pct(self.grade_c_m + self.reject_m, self.length_m)


def roll_quality(
    insp: Iterable[InspRow], defects: Iterable[DefectRow], key: Callable[[object], object],
) -> Dict[object, QualAgg]:
    """`key` is applied to both inspection rows and defect rows (they share loom/style/beam/shift/shift_date)."""
    out: Dict[object, QualAgg] = defaultdict(QualAgg)
    for r in insp:
        q = out[key(r)]
        q.rolls += r.rolls
        q.length_m += r.length_m
        q.grade_a_m += r.grade_a_m
        q.grade_b_m += r.grade_b_m
        q.grade_c_m += r.grade_c_m
        q.reject_m += r.reject_m
        q.demo += r.demo
    for d in defects:
        q = out[key(d)]
        q.defects += d.defects
        q.points += d.points
    return dict(out)


def total_quality(insp: List[InspRow], defects: List[DefectRow]) -> QualAgg:
    return roll_quality(insp, defects, lambda _r: "all").get("all", QualAgg())


# ---------------------------------------------------------------------------- impact of downtime

@dataclass(frozen=True)
class LoomImpactParams:
    run_rate_m_per_min: float  # metres woven per running minute
    contribution_per_m: float  # rupees of contribution per metre (rate - variable cost)
    basis: str  # "observed" or "rated" (fallback)


def loom_impact_params(prod_rows: List[ProdRow], refs: Refs) -> Dict[int, LoomImpactParams]:
    """
    Per loom: how fast it weaves while running, and what a metre of its fabric contributes.
    Observed from the window's own readings; when a loom has none, falls back to rated speed x the
    target efficiency of its most recent style. The basis is returned so evidence can say which.
    """
    by_loom: Dict[int, ProdAgg] = roll_production(prod_rows, lambda r: r.loom_id)
    contrib_num: Dict[int, float] = defaultdict(float)
    contrib_den: Dict[int, float] = defaultdict(float)
    last_style: Dict[int, Tuple[object, int]] = {}
    for r in prod_rows:
        if r.style_id is not None:
            contrib_num[r.loom_id] += r.meters * refs.contribution_per_m(r.style_id)
            contrib_den[r.loom_id] += r.meters
            if r.loom_id not in last_style or r.shift_date > last_style[r.loom_id][0]:
                last_style[r.loom_id] = (r.shift_date, r.style_id)
    out: Dict[int, LoomImpactParams] = {}
    for loom_id in set(by_loom) | set(refs.looms):
        agg = by_loom.get(loom_id)
        rate = agg.run_rate_m_per_min if agg else None
        sid = last_style.get(loom_id, (None, None))[1]
        contrib = contrib_num[loom_id] / contrib_den[loom_id] if contrib_den.get(loom_id) else refs.contribution_per_m(sid)
        basis = "observed"
        if rate is None:
            loom, style = refs.looms.get(loom_id), refs.styles.get(sid) if sid is not None else None
            if loom is None or style is None:
                continue
            rate = float(loom.rated_rpm) * float(style.target_efficiency_pct) / 100.0 / (float(style.ppi) * 39.3701)
            basis = "rated"
        out[loom_id] = LoomImpactParams(rate, contrib, basis)
    return out


@dataclass
class Impact:
    lost_m: float = 0.0
    lost_lakhs: float = 0.0
    assumptions: List[str] = field(default_factory=list)


def downtime_impact(stop_rows: Iterable[StopRow], params: Dict[int, LoomImpactParams], include_planned: bool = False) -> Impact:
    """Estimated metres and rupees (lakh) not produced because of the stops. An estimate, not a measurement."""
    imp = Impact()
    bases = set()
    for r in stop_rows:
        if r.is_planned and not include_planned:
            continue
        p = params.get(r.loom_id)
        if p is None:
            continue
        lost = r.downtime_s / 60.0 * p.run_rate_m_per_min
        imp.lost_m += lost
        imp.lost_lakhs += lost * p.contribution_per_m / 100_000.0
        bases.add(p.basis)
    if bases:
        imp.assumptions.append("Lost metres = downtime x the loom's average running output; rupees = lost metres x style contribution per metre.")
    if "rated" in bases:
        imp.assumptions.append("Some looms had no readings in the window, so rated speed x target efficiency was used for them.")
    return imp

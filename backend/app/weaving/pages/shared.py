"""
One request's view of the mill, shared by every page builder: the analysis context plus lazily computed, cached
findings, machine alerts and health, order risk and live floor state. Money figures are only ever produced for roles
allowed to see them (`Mill.money`); everyone else gets None, never a zero that looks like a number.
"""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import date, datetime, timedelta
from functools import cached_property
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.roles import FINANCIAL_ROLES, Role
from app.schemas.weaving_intel import Finding
from app.weaving import models as m
from app.weaving.analytics import calc, investigations, orders as orders_mod, sensors, stats
from app.weaving.analytics.context import AnalysisContext


def r1(x, n=1):
    return None if x is None else round(x, n)


class Mill:
    def __init__(self, db: Session, role: Role, period: str = "TODAY", now: Optional[datetime] = None, lens_days: int = 14):
        self.db, self.role = db, role
        self.ctx = AnalysisContext(db, now, period, lens_days)
        self.money = role in FINANCIAL_ROLES

    # --------------------------------------------------------------- shortcuts
    @property
    def refs(self):
        return self.ctx.refs

    @property
    def now(self) -> datetime:
        return self.ctx.now

    def lakhs(self, x: Optional[float]) -> Optional[float]:
        return None if (x is None or not self.money) else round(x, 2)

    # --------------------------------------------------------------- cached analytics
    @cached_property
    def findings(self) -> List[Finding]:
        return investigations.all_findings(self.ctx, include_maintenance=False)

    @cached_property
    def maintenance_findings(self) -> List[Finding]:
        rec = [f for f in self.findings if f.kind == "recurring_stop"]
        return investigations.maintenance_priorities(self.ctx, rec, self.alerts)

    @cached_property
    def alerts(self) -> List[sensors.SensorAlert]:
        return sensors.detect_alerts(self.ctx)

    @cached_property
    def pm_overdue_days(self) -> Dict[int, int]:
        E = m.WvMaintenanceEvent
        out: Dict[int, int] = {}
        for loom_id, due in self.db.execute(select(E.loom_id, E.planned_for).where(E.event_type == "PREVENTIVE", E.status == "PLANNED", E.planned_for < self.ctx.today)):
            out[loom_id] = max(out.get(loom_id, 0), (self.ctx.today - due).days)
        return out

    @cached_property
    def mech_ratio(self) -> Dict[int, float]:
        """Mechanical + electrical stops per 100k picks, relative to the median of looms of the same type."""
        ctx, refs = self.ctx, self.refs
        mech = {i for i, r in refs.reasons.items() if r.category in ("MECHANICAL", "ELECTRICAL")}
        rows = ctx.prod_between(ctx.lens_start, ctx.lens_end)
        P = calc.roll_production(rows, lambda r: r.loom_id)
        S = calc.roll_stops([r for r in ctx.stops_between(ctx.lens_start, ctx.lens_end) if r.reason_id in mech], lambda r: r.loom_id)
        rate = {l: (S[l].eligible_events / P[l].picks * 1e5 if l in S and P[l].picks > 0 else 0.0) for l in P}
        by_type: Dict[str, List[float]] = defaultdict(list)
        for l, v in rate.items():
            by_type[refs.looms[l].loom_type].append(v)
        med = {t: stats.median(v) for t, v in by_type.items()}
        return {l: (v / med[refs.looms[l].loom_type] if med[refs.looms[l].loom_type] > 0 else 0.0) for l, v in rate.items()}

    @cached_property
    def health(self) -> Dict[int, dict]:
        declines = {next((i for i, l in self.refs.looms.items() if l.loom_code == f.evidence.scope["loom"]), None) for f in self.findings if f.kind == "loom_decline"}
        return sensors.machine_health(self.ctx, self.alerts, declines - {None}, self.pm_overdue_days, self.mech_ratio)

    @cached_property
    def health_scores(self) -> Dict[int, int]:
        return {k: v["score"] for k, v in self.health.items()}

    @cached_property
    def orders(self) -> List[dict]:
        return orders_mod.order_progress(self.ctx)

    # --------------------------------------------------------------- live floor
    @cached_property
    def open_stops(self) -> Dict[int, dict]:
        E = m.WvStopEvent
        out = {}
        for e in self.db.scalars(select(E).where(E.ended_at.is_(None))):
            out[e.loom_id] = {"reason_id": e.reason_id, "since": e.started_at, "weaver_id": e.weaver_id, "fitter_id": e.fitter_id}
        return out

    @cached_property
    def assigned_looms(self) -> set:
        return set(self.db.scalars(select(m.WvOrderAssignment.loom_id).where(m.WvOrderAssignment.assigned_to.is_(None))))

    def loom_status(self, loom_id: int) -> str:
        lm = self.refs.looms[loom_id]
        if loom_id in self.open_stops:
            return "STOPPED"
        return "RUNNING" if lm.is_active and loom_id in self.assigned_looms else "IDLE"

    # --------------------------------------------------------------- daily series
    def daily(self, start: date, end: date) -> List[dict]:
        ctx = self.ctx
        P = calc.roll_production(ctx.prod_between(start, end), lambda r: r.shift_date)
        S = calc.roll_stops([r for r in ctx.stops_between(start, end) if not r.is_planned], lambda r: r.shift_date)
        out = []
        for d in sorted(P):
            p, s = P[d], S.get(d, calc.StopAgg())
            out.append({"date": d.isoformat(), "label": f"{d:%d %b}", "meters": round(p.meters), "target_m": round(p.target_meters), "efficiency_pct": r1(p.efficiency_pct), "utilization_pct": r1(p.utilization_pct),
                        "stops_per_100k": r1(s.per_100k_picks(p.picks), 2), "downtime_min": round(s.unplanned_downtime_min), "complete": d < ctx.today})
        return out

    def finding_dicts(self, findings: List[Finding]) -> List[dict]:
        dicts = [f.model_dump() for f in findings]
        if not self.money:
            for d in dicts:
                if d["evidence"].get("estimated_impact"):
                    d["evidence"]["estimated_impact"]["lost_lakhs"] = None
        return dicts

    def for_me(self, findings: List[Finding]) -> List[Finding]:
        return [f for f in findings if self.role.value in f.audiences]


def kpi(label: str, value, unit: str = "", prev=None, good_when: str = "up", spark: Optional[List[float]] = None, hint: str = "", status: Optional[str] = None, decimals: int = 1) -> dict:
    """A headline number with its change against the comparison period and a sparkline."""
    delta = None
    if value is not None and prev not in (None, 0):
        delta = round(value - prev, decimals) if unit in ("%", "pts") else round((value - prev) / abs(prev) * 100, 1)
    return {"label": label, "value": None if value is None else round(value, decimals), "unit": unit, "delta": delta, "delta_unit": "pts" if unit in ("%", "pts") else "%", "good_when": good_when,
            "spark": [round(x, decimals) for x in (spark or []) if x is not None], "hint": hint, "status": status}


def brief_line(severity: str, text: str, link: str, kind: str, impact_lakhs: Optional[float] = None) -> dict:
    return {"severity": severity, "text": text, "link": link, "kind": kind, "impact_lakhs": impact_lakhs}

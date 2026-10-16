"""Machines (fleet watch and per-machine detail) and the Maintenance Desk."""
from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from typing import Dict, List, Optional

from sqlalchemy import select

from app.core.exceptions import NotFoundException
from app.weaving import models as m
from app.weaving.analytics import calc, sensors, stats
from app.weaving.pages.shared import Mill, kpi, r1


def _loom_by_code(mill: Mill, code: str):
    for i, l in mill.refs.looms.items():
        if l.loom_code == code:
            return i, l
    raise NotFoundException(f"No loom {code}")


def _next_pm(mill: Mill) -> Dict[int, dict]:
    E = m.WvMaintenanceEvent
    out: Dict[int, dict] = {}
    for e in mill.db.scalars(select(E).where(E.event_type == "PREVENTIVE", E.status == "PLANNED").order_by(E.planned_for)):
        if e.loom_id not in out:
            out[e.loom_id] = {"task": e.task, "due": e.planned_for.isoformat(), "overdue_days": max(0, (mill.ctx.today - e.planned_for).days)}
    return out


def fleet(mill: Mill) -> dict:
    ctx, refs = mill.ctx, mill.refs
    end = ctx.window.end_date
    prod = ctx.prod_between(end - timedelta(days=13), end)
    P = calc.roll_production(prod, lambda r: r.loom_id)
    S = calc.roll_stops([r for r in ctx.stops_between(end - timedelta(days=13), end) if not r.is_planned], lambda r: r.loom_id)
    npm = _next_pm(mill)
    P_ls = calc.roll_production(prod, lambda r: (r.loom_id, r.style_id))
    dom = {}
    for (lid, sid), a in P_ls.items():
        if lid not in dom or a.meters > P_ls[(lid, dom[lid])].meters:
            dom[lid] = sid
    alerts_by: Dict[int, List] = defaultdict(list)
    for a in mill.alerts:
        alerts_by[a.loom_id].append(a)
    rows = []
    for lid, lm in sorted(refs.looms.items(), key=lambda kv: kv[1].loom_code):
        p, s = P.get(lid), S.get(lid)
        h = mill.health.get(lid)
        stop = mill.open_stops.get(lid)
        al = alerts_by.get(lid, [])
        rows.append({
            "loom": lm.loom_code, "type": lm.loom_type, "make": lm.make, "model": lm.model, "serial_no": lm.serial_no, "year": lm.year_of_make, "age_years": (ctx.today.year - lm.year_of_make) if lm.year_of_make else None,
            "bay": lm.bay, "shedding": lm.shedding, "colours": lm.colours, "reed_space_cm": float(lm.reed_space_cm) if lm.reed_space_cm else None, "rated_rpm": lm.rated_rpm,
            "power_kw": float(lm.power_kw_rated) if lm.power_kw_rated else None, "last_overhaul": lm.last_overhaul_on.isoformat() if lm.last_overhaul_on else None,
            "days_since_overhaul": (ctx.today - lm.last_overhaul_on).days if lm.last_overhaul_on else None, "warranty_until": lm.warranty_until.isoformat() if lm.warranty_until else None,
            "status": mill.loom_status(lid), "stopped_min": int((mill.now - stop["since"]).total_seconds() / 60) if stop else 0, "stop_reason": refs.reasons[stop["reason_id"]].name if stop else None,
            "style": refs.style_code(dom.get(lid)), "efficiency_pct": r1(p.efficiency_pct) if p else None, "stops_per_100k": r1(s.per_100k_picks(p.picks), 2) if s and p else None,
            "health": h["score"] if h else None, "band": h["band"] if h else None, "alerts": [{"level": a.level, "title": a.title, "kind": a.kind} for a in al],
            "next_pm": npm.get(lid), "running_hours_14d": round(p.running_h) if p else None,
        })
    levels = defaultdict(int)
    for a in mill.alerts:
        levels[a.level] += 1
    sensor_rows = [r for r in ctx.sensor_days if r.shift_date >= end - timedelta(days=1)]
    online = sum(r.with_sensors for r in sensor_rows) / max(sum(r.readings for r in sensor_rows), 1) * 100
    return {"as_of": mill.now.isoformat(), "kpis": [
                kpi("Healthy", float(sum(1 for r in rows if r["band"] == "HEALTHY")), "of " + str(len(rows)), None, "up", [], "health score 80+", decimals=0),
                kpi("Watch", float(sum(1 for r in rows if r["band"] == "WATCH")), "", None, "down", [], "score 60–79", decimals=0, status="warn" if any(r["band"] == "WATCH" for r in rows) else "ok"),
                kpi("At risk", float(sum(1 for r in rows if r["band"] == "AT_RISK")), "", None, "down", [], "score under 60", decimals=0, status="bad" if any(r["band"] == "AT_RISK" for r in rows) else "ok"),
                kpi("Active alerts", float(len(mill.alerts)), "", None, "down", [], f"{levels['CRITICAL']} critical · {levels['WARNING']} warning · {levels['WATCH']} watch", decimals=0),
                kpi("Sensors online", online, "%", None, "up", [], "last 2 days")],
            "alerts": [a.as_dict() for a in mill.alerts], "looms": rows,
            "method": ["Each loom is compared with its OWN normal level, not a fixed number.", "Alerts are early-warning signals from vibration, temperature, air pressure and power. They have not been validated against real breakdowns.",
                       sensors.HEALTH_NOTE]}


def detail(mill: Mill, code: str) -> dict:
    ctx, refs = mill.ctx, mill.refs
    lid, lm = _loom_by_code(mill, code)
    end = ctx.window.end_date
    start = end - timedelta(days=20)
    charts = []
    for key, spec in sensors.SPECS.items():
        if key == "pressure" and lm.loom_type != "Airjet":
            continue
        series = sensors.daily_series(ctx, lid, key)
        if not series:
            continue
        values = [v for _, v in series]
        lvl = sensors._normal_level(values, spec)
        charts.append({"key": key, "label": spec.label, "unit": spec.unit, "alarm": spec.alarm, "worse": spec.worse,
                       "normal": {"center": round(lvl["center"], 2), "low": round(lvl["center"] - 3 * lvl["spread"], 2), "high": round(lvl["center"] + 3 * lvl["spread"], 2)} if lvl else None,
                       "points": [{"date": d.isoformat(), "label": f"{d:%d %b}", "value": round(v, 2)} for d, v in series if d >= start]})
    prod = ctx.prod_between(end - timedelta(days=13), end)
    mine = [r for r in prod if r.loom_id == lid]
    D = calc.roll_production(mine, lambda r: r.shift_date)
    stops14 = [r for r in ctx.stops_between(end - timedelta(days=13), end) if r.loom_id == lid]
    SD = calc.roll_stops([r for r in stops14 if not r.is_planned], lambda r: r.shift_date)
    perf = [{"label": f"{d:%d %b}", "efficiency_pct": r1(a.efficiency_pct), "stops_per_100k": r1(SD[d].per_100k_picks(a.picks), 2) if d in SD else 0.0} for d, a in sorted(D.items())]
    by_reason = calc.roll_stops(stops14, lambda r: r.reason_id)
    causes = [{"cause": refs.reasons[i].name, "category": refs.reasons[i].category, "planned": refs.reasons[i].is_planned, "stops": a.events, "downtime_min": round(a.downtime_min)} for i, a in sorted(by_reason.items(), key=lambda kv: -kv[1].downtime_s) if a.downtime_s > 0]
    E, MV = m.WvStopEvent, m.WvMaintenanceEvent
    recent = mill.db.execute(select(E, m.WvStopReason.name, m.WvStopReason.category).join(m.WvStopReason, m.WvStopReason.id == E.reason_id).where(E.loom_id == lid).order_by(E.started_at.desc()).limit(12)).all()
    pm = mill.db.scalars(select(MV).where(MV.loom_id == lid, MV.event_type == "PREVENTIVE").order_by(MV.planned_for.desc()).limit(6)).all()
    bds = mill.db.scalars(select(MV).where(MV.loom_id == lid, MV.event_type == "BREAKDOWN").order_by(MV.started_at.desc()).limit(6)).all()
    tot = calc.total_production(mine)
    breakdowns14 = [b for b in mill.db.scalars(select(MV).where(MV.loom_id == lid, MV.event_type == "BREAKDOWN", MV.started_at >= ctx.cal.day_bounds(end - timedelta(days=13))[0]))]
    done = [(b.completed_at - b.started_at).total_seconds() / 60 for b in breakdowns14 if b.completed_at]
    f = fleet_row = next((r for r in fleet(mill)["looms"] if r["loom"] == code), None)
    assign = mill.db.execute(select(m.WvProductionOrder.order_no, m.WvCustomer.name).join(m.WvOrderAssignment, m.WvOrderAssignment.order_id == m.WvProductionOrder.id).outerjoin(m.WvCustomer, m.WvCustomer.id == m.WvProductionOrder.customer_id)
                             .where(m.WvOrderAssignment.loom_id == lid, m.WvOrderAssignment.assigned_to.is_(None))).first()
    return {"as_of": mill.now.isoformat(), "spec": f, "health": mill.health.get(lid), "alerts": [a.as_dict() for a in mill.alerts if a.loom_id == lid], "sensors": charts, "performance": perf, "causes": causes,
            "order": {"order_no": assign[0], "customer": assign[1]} if assign else None,
            "reliability": {"breakdowns_14d": len(breakdowns14), "mtbf_hours": r1(tot.running_h / len(breakdowns14), 1) if breakdowns14 else None, "mttr_min": round(sum(done) / len(done)) if done else None},
            "maintenance": {"preventive": [{"task": e.task, "planned_for": e.planned_for.isoformat() if e.planned_for else None, "status": e.status, "overdue_days": max(0, (ctx.today - e.planned_for).days) if e.status == "PLANNED" and e.planned_for else 0} for e in pm],
                            "breakdowns": [{"task": b.task, "started_at": b.started_at.isoformat() if b.started_at else None, "minutes": round((b.completed_at - b.started_at).total_seconds() / 60) if b.completed_at and b.started_at else None, "status": b.status} for b in bds]},
            "recent_stops": [{"started_at": e.started_at.isoformat(), "minutes": round((e.ended_at - e.started_at).total_seconds() / 60, 1) if e.ended_at else None, "open": e.ended_at is None, "reason": n, "category": c} for e, n, c in recent]}


def maintenance(mill: Mill) -> dict:
    ctx, refs = mill.ctx, mill.refs
    end = ctx.window.end_date
    E = m.WvMaintenanceEvent
    pm = mill.db.execute(select(E, m.WvLoom.loom_code).join(m.WvLoom, m.WvLoom.id == E.loom_id).where(E.event_type == "PREVENTIVE", E.planned_for.isnot(None), E.planned_for >= ctx.today - timedelta(days=60), E.planned_for <= ctx.today + timedelta(days=14)).order_by(E.planned_for)).all()
    board, overdue, upcoming = [], 0, 0
    for e, code in pm:
        if e.status in ("COMPLETED", "CANCELLED"):
            continue
        od = (ctx.today - e.planned_for).days
        st = "OVERDUE" if od > 0 else "TODAY" if od == 0 else "UPCOMING"
        overdue += st == "OVERDUE"
        upcoming += st != "OVERDUE"
        board.append({"loom": code, "task": e.task, "due": e.planned_for.isoformat(), "days": od, "state": st, "health": mill.health[e.loom_id]["score"] if e.loom_id in mill.health else None})
    done = [p for p in pm if p[0].planned_for <= ctx.today and p[0].status != "CANCELLED"]
    compliance = round(sum(1 for p in done if p[0].status == "COMPLETED") / len(done) * 100, 1) if done else None
    start_at = ctx.cal.day_bounds(end - timedelta(days=13))[0]
    bds = mill.db.execute(select(E, m.WvLoom.loom_code).join(m.WvLoom, m.WvLoom.id == E.loom_id).where(E.event_type == "BREAKDOWN", E.started_at >= start_at).order_by(E.started_at.desc())).all()
    prod14 = calc.total_production(ctx.prod_between(end - timedelta(days=13), end))
    mins = [(e.completed_at - e.started_at).total_seconds() / 60 for e, _ in bds if e.completed_at]
    by_day: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
    for e, _ in bds:
        d = e.started_at.astimezone(ctx.cal.tz)
        key = f"{d:%d %b}"
        by_day[key][0] += 1
        by_day[key][1] += round((e.completed_at - e.started_at).total_seconds() / 60) if e.completed_at else 0
    days = [f"{(end - timedelta(days=i)):%d %b}" for i in range(13, -1, -1)]
    priorities = mill.maintenance_findings
    ranked = [{"loom": f.evidence.scope["loom"], "score": f.priority_score, "severity": f.severity, "confidence": f.confidence.level, "facts": f.facts, "steps": f.next_steps, "link": f.link,
               "health": next((h["score"] for i, h in mill.health.items() if refs.loom_code(i) == f.evidence.scope["loom"]), None)} for f in priorities[:8]]
    watch = sorted([(mill.health[i]["score"], refs.loom_code(i)) for i in mill.health if mill.health[i]["band"] != "HEALTHY"])
    return {"as_of": mill.now.isoformat(),
            "kpis": [kpi("Breakdowns (14 days)", float(len(bds)), "", None, "down", [by_day[d][0] for d in days], f"{len(mins)} repaired", decimals=0),
                     kpi("MTBF", prod14.running_h / len(bds) if bds else None, "h", None, "up", [], "running hours per breakdown", decimals=1),
                     kpi("MTTR", sum(mins) / len(mins) if mins else None, "min", None, "down", [], "mean time to repair", decimals=0),
                     kpi("PM compliance", compliance, "%", None, "up", [], "planned jobs done by their due date"),
                     kpi("PM overdue", float(overdue), "", None, "down", [], f"{upcoming} due in the next 14 days", decimals=0, status="bad" if overdue else "ok")],
            "priorities": ranked, "alerts": [a.as_dict() for a in mill.alerts if a.kind != "SENSOR_OFFLINE" or True][:12], "pm_board": board,
            "breakdowns": [{"loom": code, "task": e.task, "started_at": e.started_at.isoformat(), "minutes": round((e.completed_at - e.started_at).total_seconds() / 60) if e.completed_at else None, "status": e.status} for e, code in bds[:15]],
            "breakdown_trend": [{"label": d, "breakdowns": by_day[d][0], "downtime_min": by_day[d][1]} for d in days],
            "watchlist": [{"loom": c, "health": s} for s, c in watch],
            "notes": ["A breakdown is a mechanical or electrical stop of at least 30 minutes that maintenance attended.", "Priorities combine open stoppages, overdue preventive maintenance and repeated mechanical/electrical stops; see the method on each card."]}

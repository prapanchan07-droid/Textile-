"""Workforce, the Shift Cockpit (supervisor), and the Shift Handover."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select

from app.core.roles import Role
from app.weaving import models as m
from app.weaving.analytics import calc, facts, workforce
from app.weaving.pages.shared import Mill, kpi, r1


def workforce_page(mill: Mill) -> dict:
    ctx = mill.ctx
    only = None
    if mill.role == Role.SHIFT_SUPERVISOR:
        _, shift = ctx.cal.shift_at(mill.now)
        only = shift.id
    data = workforce.build(ctx, include_contact=mill.role in (Role.OWNER, Role.WEAVING_MANAGER, Role.SHIFT_SUPERVISOR), only_shift_id=only)
    data["scope"] = "Your shift's crew" if only else "All shifts"
    return {"as_of": mill.now.isoformat(), **data}


def _shift_now(mill: Mill, which: str = "current") -> Tuple[date, object]:
    cal = mill.ctx.cal
    day, shift = cal.shift_at(mill.now)
    if which == "previous":
        start, _ = cal.shift_bounds(day, shift)
        day, shift = cal.shift_at(start - timedelta(minutes=5))
    return day, shift


def _notes(mill: Mill, day: date, shift) -> List[dict]:
    N = m.WvShiftNote
    refs = mill.refs
    since = day - timedelta(days=3)
    rows = mill.db.scalars(select(N).where(N.shift_date >= since).order_by(N.created_at.desc())).all()
    out = []
    for n in rows:
        mine = n.shift_date == day and n.shift_id == shift.id
        if not mine and n.resolved_at is not None:
            continue
        out.append({"id": n.id, "ref": n.note_ref, "shift": refs.shift_name(n.shift_id), "date": n.shift_date.isoformat(), "loom": refs.loom_code(n.loom_id) if n.loom_id else None, "category": n.category,
                    "severity": n.severity, "body": n.body, "author": n.author_name, "created_at": n.created_at.isoformat(), "resolved": n.resolved_at is not None, "this_shift": mine})
    return out


def _roster(mill: Mill, day: date, shift) -> dict:
    refs = mill.refs
    att = mill.db.execute(select(m.WvAttendance.operator_id, m.WvAttendance.status).where(m.WvAttendance.shift_date == day, m.WvAttendance.shift_id == shift.id)).all()
    status = {a[0]: a[1] for a in att}
    asg = mill.db.execute(select(m.WvShiftAssignment.operator_id, m.WvShiftAssignment.loom_id, m.WvShiftAssignment.assignment_role).where(m.WvShiftAssignment.shift_date == day, m.WvShiftAssignment.shift_id == shift.id)).all()
    looms_of: Dict[int, List[str]] = defaultdict(list)
    role_of = {}
    for oid, lid, role in asg:
        looms_of[oid].append(refs.loom_code(lid))
        role_of[oid] = role
    people = []
    for oid, st in status.items():
        o = refs.operators[oid]
        people.append({"code": o.employee_code, "name": o.full_name, "role": o.operator_role, "designation": o.designation, "status": st, "looms": sorted(looms_of.get(oid, [])), "grade": o.grade})
    covering = []
    for oid, lst in looms_of.items():
        o = refs.operators[oid]
        if role_of.get(oid) == "WEAVER" and len(lst) > 4:
            covering.append({"name": o.full_name, "code": o.employee_code, "looms": sorted(lst)})
    people.sort(key=lambda p: (p["role"], p["status"] != "PRESENT", p["code"]))
    return {"people": people, "present": sum(1 for p in people if p["status"] == "PRESENT"), "absent": sum(1 for p in people if p["status"] != "PRESENT"), "overloaded": covering}


def _shift_stats(mill: Mill, day: date, shift) -> dict:
    ctx, refs = mill.ctx, mill.refs
    rows = [r for r in ctx.prod_between(day, day) if r.shift_id == shift.id]
    agg = calc.total_production(rows)
    all_day = calc.total_production(ctx.prod_between(day - timedelta(days=6), day - timedelta(days=1)))
    stops = [r for r in ctx.stops_between(day, day) if r.shift_id == shift.id and not r.is_planned]
    s = calc.total_stops(stops)
    by = calc.roll_stops(stops, lambda r: r.reason_id)
    top = [{"cause": refs.reasons[i].name, "downtime_min": round(a.downtime_min), "stops": a.events} for i, a in sorted(by.items(), key=lambda kv: -kv[1].downtime_s)[:5]]
    per_loom = calc.roll_production(rows, lambda r: r.loom_id)
    return {"agg": agg, "stops": s, "top_causes": top, "per_loom": per_loom, "baseline_eff": all_day.efficiency_pct}


def cockpit(mill: Mill) -> dict:
    ctx, refs = mill.ctx, mill.refs
    day, shift = _shift_now(mill)
    start, end = ctx.cal.shift_bounds(day, shift)
    elapsed = max(0.0, min(1.0, (mill.now - start).total_seconds() / (end - start).total_seconds()))
    st = _shift_stats(mill, day, shift)
    agg = st["agg"]
    hours = [h for h in facts.load_hourly(mill.db, day) if h.shift_id == shift.id]
    cum_a = cum_p = 0.0
    chart = []
    for h in hours:
        cum_a += h.meters
        cum_p += h.target_m
        chart.append({"hour": f"{h.start.astimezone(ctx.cal.tz):%H:%M}", "actual_m": round(h.meters), "plan_m": round(h.target_m), "cum_actual_m": round(cum_a), "cum_plan_m": round(cum_p)})
    roster = _roster(mill, day, shift)
    weaver_of = {}
    for r in ctx.prod_between(day, day):
        if r.shift_id == shift.id and r.weaver_id:
            weaver_of[r.loom_id] = refs.operators[r.weaver_id].full_name
    alerts_by = defaultdict(list)
    for a in mill.alerts:
        alerts_by[a.loom_id].append(a)
    floor = []
    for lid, lm in sorted(refs.looms.items(), key=lambda kv: kv[1].loom_code):
        p = st["per_loom"].get(lid)
        stop = mill.open_stops.get(lid)
        floor.append({"loom": lm.loom_code, "type": lm.loom_type, "status": mill.loom_status(lid), "efficiency_pct": r1(p.efficiency_pct) if p else None, "weaver": weaver_of.get(lid),
                      "reason": refs.reasons[stop["reason_id"]].name if stop else None, "stopped_min": int((mill.now - stop["since"]).total_seconds() / 60) if stop else 0,
                      "health": mill.health[lid]["score"] if lid in mill.health else None, "alerts": [a.level for a in alerts_by.get(lid, [])]})
    from app.weaving.pages.overview import _stopped_now
    watch = [{"loom": a.loom, "title": a.title, "level": a.level, "fact": a.facts[0]} for a in mill.alerts if a.level in ("CRITICAL", "WARNING")][:5]
    A = m.WvAction
    actions = [{"ref": a.action_ref, "issue": a.issue, "action": a.action, "owner": a.owner_name, "due": a.due_date.isoformat() if a.due_date else None, "status": a.status}
               for a in mill.db.scalars(select(A).where(A.status.in_(("OPEN", "IN_PROGRESS"))).order_by(A.due_date).limit(6))]
    pace_plan = agg.target_meters
    return {"as_of": mill.now.isoformat(), "shift": {"name": shift.name, "date": day.isoformat(), "start": start.astimezone(ctx.cal.tz).strftime("%H:%M"), "end": end.astimezone(ctx.cal.tz).strftime("%H:%M"), "elapsed_pct": round(elapsed * 100)},
            "kpis": [kpi("Output so far", agg.meters, "m", None, "up", [c["actual_m"] for c in chart], f"plan so far {pace_plan:,.0f} m", decimals=0),
                     kpi("Against plan", agg.achievement_pct, "%", None, "up", [], "output / plan for the hours worked"),
                     kpi("Efficiency", agg.efficiency_pct, "%", st["baseline_eff"], "up", [], "vs the last 7 days"),
                     kpi("Stops this shift", float(st["stops"].events), "", None, "down", [], f"{st['stops'].avg_duration_min or 0:.1f} min average", decimals=0),
                     kpi("Stopped now", float(len(mill.open_stops)), "", None, "down", [], "looms", decimals=0, status="warn" if mill.open_stops else "ok")],
            "chart": chart, "floor": floor, "stopped_now": _stopped_now(mill), "top_causes": st["top_causes"], "watch": watch, "roster": roster, "notes": _notes(mill, day, shift), "actions": actions,
            "findings": mill.finding_dicts([f for f in mill.for_me(mill.findings)][:3])}


def handover(mill: Mill, which: str = "current") -> dict:
    ctx, refs = mill.ctx, mill.refs
    day, shift = _shift_now(mill, which)
    start, end = ctx.cal.shift_bounds(day, shift)
    st = _shift_stats(mill, day, shift)
    agg, s = st["agg"], st["stops"]
    roster = _roster(mill, day, shift)
    notes = [n for n in _notes(mill, day, shift)]
    longest = []
    E = m.WvStopEvent
    rows = mill.db.execute(select(E, m.WvLoom.loom_code, m.WvStopReason.name).join(m.WvLoom, m.WvLoom.id == E.loom_id).join(m.WvStopReason, m.WvStopReason.id == E.reason_id)
                           .where(E.shift_date == day, E.shift_id == shift.id, m.WvStopReason.is_planned.is_(False))).all()
    for e, code, reason in rows:
        mins = ((e.ended_at or mill.now) - e.started_at).total_seconds() / 60
        longest.append({"loom": code, "reason": reason, "minutes": round(mins), "open": e.ended_at is None, "at": e.started_at.astimezone(ctx.cal.tz).strftime("%H:%M")})
    longest.sort(key=lambda x: -x["minutes"])
    per_loom = [(a.efficiency_pct, refs.loom_code(l), a) for l, a in st["per_loom"].items() if a.efficiency_pct is not None]
    per_loom.sort()
    narrative = []
    if agg.target_meters:
        narrative.append(f"{shift.name} wove {agg.meters:,.0f} m, {agg.achievement_pct:.0f}% of plan, at {agg.efficiency_pct:.1f}% efficiency"
                         + (f" ({agg.efficiency_pct - st['baseline_eff']:+.1f} points against the last 7 days)." if st["baseline_eff"] else "."))
    if st["top_causes"]:
        narrative.append("Most downtime: " + ", ".join(f"{c['cause'].lower()} ({c['downtime_min']} min)" for c in st["top_causes"][:3]) + ".")
    if longest:
        l = longest[0]
        narrative.append(f"Longest stop: {l['loom']} for {l['minutes']} minutes ({l['reason'].lower()}) at {l['at']}" + (", still open." if l["open"] else "."))
    if per_loom:
        narrative.append(f"Weakest looms this shift: " + ", ".join(f"{c} ({e:.0f}%)" for e, c, _ in per_loom[:3]) + ".")
    for a in mill.alerts:
        if a.level in ("CRITICAL", "WARNING"):
            narrative.append(f"Machine watch: {a.title}. {a.facts[0]}")
            if len([x for x in narrative if x.startswith('Machine watch')]) >= 2:
                break
    if roster["absent"]:
        narrative.append(f"{roster['absent']} of {len(roster['people'])} crew absent" + (f"; {', '.join(o['name'] + ' covers ' + str(len(o['looms'])) + ' looms' for o in roster['overloaded'])}." if roster["overloaded"] else "."))
    carry = [n for n in notes if n["severity"] in ("WARNING", "URGENT") and not n["resolved"]]
    A = m.WvAction
    open_actions = [{"ref": a.action_ref, "issue": a.issue, "owner": a.owner_name, "due": a.due_date.isoformat() if a.due_date else None, "status": a.status}
                    for a in mill.db.scalars(select(A).where(A.status.in_(("OPEN", "IN_PROGRESS"))).order_by(A.due_date).limit(8))]
    return {"as_of": mill.now.isoformat(), "which": which, "complete": end <= mill.now, "shift": {"name": shift.name, "date": day.isoformat(), "start": start.astimezone(ctx.cal.tz).strftime("%H:%M"), "end": end.astimezone(ctx.cal.tz).strftime("%H:%M")},
            "narrative": narrative, "kpis": {"meters": round(agg.meters), "plan_m": round(agg.target_meters), "achievement_pct": r1(agg.achievement_pct), "efficiency_pct": r1(agg.efficiency_pct), "stops": s.events, "avg_stop_min": r1(s.avg_duration_min), "downtime_min": round(s.unplanned_downtime_min)},
            "top_causes": st["top_causes"], "longest_stops": longest[:6], "weakest": [{"loom": c, "efficiency_pct": r1(e)} for e, c, _ in per_loom[:5]], "roster": roster, "notes": notes, "carry_over": carry, "actions": open_actions,
            "watch": [{"loom": a.loom, "title": a.title, "level": a.level} for a in mill.alerts if a.level in ("CRITICAL", "WARNING")][:5]}

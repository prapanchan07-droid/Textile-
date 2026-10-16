"""
Workforce analytics: who is on the floor, how often people are present, how their looms perform, and where coverage
or skills are thin. No pay data is held. Performance figures describe the looms a person ran in their shifts, which
differ in age, style and condition, so they are context for a conversation, never a verdict.
"""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List, Optional

from sqlalchemy import select

from app.weaving import models as m
from app.weaving.analytics import calc, stats
from app.weaving.analytics.context import AnalysisContext

LOOMS_PER_WEAVER = 4
LOOMS_PER_FITTER = 12
DAYS = 14


def _r(x, n=1):
    return None if x is None else round(x, n)


def build(ctx: AnalysisContext, include_contact: bool, only_shift_id: Optional[int] = None) -> dict:
    refs, cal, now = ctx.refs, ctx.cal, ctx.now
    end = ctx.window.end_date
    start = end - timedelta(days=DAYS - 1)
    ops = [o for o in refs.operators.values() if o.is_active]
    att = ctx.db.execute(select(m.WvAttendance.operator_id, m.WvAttendance.shift_date, m.WvAttendance.shift_id, m.WvAttendance.status).where(m.WvAttendance.shift_date.between(start, end))).all()
    started = {s.id for s in cal.shifts if cal.shift_bounds(end, s)[0] <= now}
    att = [a for a in att if a[1] < end or a[2] in started]  # ignore shifts that have not started yet
    by_op: Dict[int, List[tuple]] = defaultdict(list)
    for a in att:
        by_op[a[0]].append(a)

    prod = ctx.prod_between(start, end)
    stops = [r for r in ctx.stops_between(start, end) if not r.is_planned]
    P = calc.roll_production([r for r in prod if r.weaver_id], lambda r: r.weaver_id)
    S = calc.roll_stops([r for r in stops if r.weaver_id], lambda r: r.weaver_id)
    loom_sets: Dict[int, set] = defaultdict(set)
    shift_days: Dict[int, set] = defaultdict(set)
    for r in prod:
        if r.weaver_id:
            loom_sets[r.weaver_id].add(refs.loom_code(r.loom_id))
            shift_days[r.weaver_id].add((r.shift_date, r.shift_id))
    type_eff = calc.total_production([r for r in prod if r.weaver_id]).efficiency_pct
    warp_ids = {i for i, r in refs.reasons.items() if r.category == "WARP"}
    weft_ids = {i for i, r in refs.reasons.items() if r.category == "WEFT"}
    SW = calc.roll_stops([r for r in stops if r.weaver_id and r.reason_id in warp_ids], lambda r: r.weaver_id)
    SF = calc.roll_stops([r for r in stops if r.weaver_id and r.reason_id in weft_ids], lambda r: r.weaver_id)
    # Expected stops for a weaver = the picks they wove on each loom x that loom's stop rate over ALL weavers, so a weaver is
    # compared with what anyone gets on the same looms (this keeps a faulty loom from being blamed on its weaver).
    picks_wl = calc.roll_production([r for r in prod if r.weaver_id], lambda r: (r.weaver_id, r.loom_id))
    picks_l = calc.roll_production([r for r in prod if r.weaver_id], lambda r: r.loom_id)
    loom_rate = {}
    for cat, ids in (("weft", weft_ids), ("warp", warp_ids)):
        ev = calc.roll_stops([r for r in stops if r.weaver_id and r.reason_id in ids], lambda r: r.loom_id)
        loom_rate[cat] = {l: (ev[l].eligible_events / picks_l[l].picks if l in ev and picks_l[l].picks > 0 else 0.0) for l in picks_l}
    expected = {cat: defaultdict(float) for cat in loom_rate}
    for (w, l), a in picks_wl.items():
        for cat in loom_rate:
            expected[cat][w] += a.picks * loom_rate[cat].get(l, 0.0)

    directory, coaching = [], []
    for o in sorted(ops, key=lambda x: (x.home_shift_id or 0, x.operator_role, x.employee_code)):
        if only_shift_id is not None and o.home_shift_id != only_shift_id:
            continue
        rows = by_op.get(o.id, [])
        tracked = len(rows)
        present = sum(1 for a in rows if a[3] == "PRESENT")
        rec = {
            "code": o.employee_code, "name": o.full_name, "role": o.operator_role, "designation": o.designation, "department": o.department, "grade": o.grade,
            "shift": refs.shift_name(o.home_shift_id) if o.home_shift_id else None, "contract": o.contract_type, "experience_years": float(o.experience_years) if o.experience_years is not None else None,
            "skills": [x for x in (o.skills or "").split(",") if x], "joined_on": o.joined_on.isoformat() if o.joined_on else None,
            "attendance_pct": _r(present / tracked * 100) if tracked else None, "days_tracked": tracked,
            "absent_days": sum(1 for a in rows if a[3] != "PRESENT"),
            "phone": o.phone if include_contact else None,
        }
        if o.operator_role == "WEAVER":
            p, s = P.get(o.id), S.get(o.id)
            if p and p.picks > 0:
                rec.update(efficiency_pct=_r(p.efficiency_pct), vs_floor_pts=_r(p.efficiency_pct - type_eff) if type_eff else None, meters=round(p.meters), shifts_worked=len(shift_days[o.id]),
                           meters_per_shift=round(p.meters / max(len(shift_days[o.id]), 1)), looms=sorted(loom_sets[o.id]), stops_per_100k=_r(s.per_100k_picks(p.picks), 2) if s else 0.0,
                           weft_stops_per_100k=_r(SF[o.id].per_100k_picks(p.picks), 2) if o.id in SF else 0.0, warp_stops_per_100k=_r(SW[o.id].per_100k_picks(p.picks), 2) if o.id in SW else 0.0)
                # a supportive flag, only when a weaver's stops are clearly above what anyone gets on the same looms
                for cat, agg_map, label in (("weft", SF, "weft stops"), ("warp", SW, "warp stops")):
                    a = agg_map.get(o.id)
                    exp = expected[cat].get(o.id, 0.0)
                    if a and a.eligible_events >= 25 and exp > 0:
                        ratio = a.eligible_events / exp
                        pv = stats.poisson_sf(a.eligible_events, exp)
                        if ratio >= 1.3 and pv < 0.001:
                            coaching.append({"code": o.employee_code, "name": o.full_name, "shift": rec["shift"], "grade": o.grade, "experience_years": rec["experience_years"], "topic": label,
                                             "observed": f"{a.eligible_events} {label} where the same looms give {exp:.0f} on average ({ratio:.1f}x, p ≈ {pv:.2g})",
                                             "suggestion": f"Pair with a senior weaver for a shift and review {cat} handling (knotting, nozzle and feeder checks). The comparison already allows for which looms they ran."})
        directory.append(rec)

    # --- shift coverage today
    n_looms = len([l for l in refs.looms.values() if l.is_active])
    coverage = []
    for s in cal.shifts:
        if s.id not in started:
            continue
        for role, norm, label in (("WEAVER", LOOMS_PER_WEAVER, "Weavers"), ("FITTER", LOOMS_PER_FITTER, "Fitters")):
            required = math.ceil(n_looms / norm)
            rows = [a for a in att if a[2] == s.id and a[1] == end and refs.operators[a[0]].operator_role == role]
            pres = sum(1 for a in rows if a[3] == "PRESENT")
            coverage.append({"shift": s.name, "role": label, "required": required, "present": pres, "absent": len(rows) - pres, "gap": required - pres,
                             "status": "CRITICAL" if required - pres >= 2 else "ATTENTION" if required - pres >= 1 else "NORMAL"})
    # --- absenteeism patterns (weavers and fitters, who have attendance records)
    daily = defaultdict(lambda: [0, 0])
    heat = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for oid, d, sid, status in att:
        daily[d][1] += 1
        daily[d][0] += status != "PRESENT"
        heat[d.weekday()][sid][1] += 1
        heat[d.weekday()][sid][0] += status != "PRESENT"
    absent_daily = [{"date": d.isoformat(), "absent_pct": _r(v[0] / v[1] * 100) if v[1] else None, "absent": v[0], "records": v[1]} for d, v in sorted(daily.items())]
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    heat_rows = [{"weekday": weekdays[w], "values": {refs.shift_name(sid): (_r(v[0] / v[1] * 100) if v[1] else None) for sid, v in sorted(heat[w].items(), key=lambda kv: refs.shifts[kv[0]].sort_order)}} for w in sorted(heat)]
    # --- skills coverage
    skill_rows = []
    for skill in ("Airjet", "Sulzer"):
        per_shift = {}
        for s in sorted(refs.shifts.values(), key=lambda x: x.sort_order):
            w = [o for o in ops if o.operator_role == "WEAVER" and o.home_shift_id == s.id and skill in (o.skills or "")]
            per_shift[s.name] = len(w)
        skill_rows.append({"skill": f"{skill} weaving", "per_shift": per_shift, "thin": min(per_shift.values()) < 3 if per_shift else False})
    weavers = [d for d in directory if d["role"] == "WEAVER"]
    present_today = sum(1 for a in att if a[1] == end and a[3] == "PRESENT")
    recs_today = sum(1 for a in att if a[1] == end)
    top = sorted([w for w in weavers if w.get("efficiency_pct") is not None], key=lambda w: -w["efficiency_pct"])
    kpis = {
        "headcount": len(ops), "by_role": {r: sum(1 for o in ops if o.operator_role == r) for r in ("WEAVER", "FITTER", "SUPERVISOR", "INSPECTOR", "TECHNICIAN")},
        "permanent_pct": _r(sum(1 for o in ops if o.contract_type == "PERMANENT") / max(len(ops), 1) * 100), "present_today": present_today, "tracked_today": recs_today,
        "absenteeism_14d_pct": _r(sum(v[0] for v in daily.values()) / max(sum(v[1] for v in daily.values()), 1) * 100),
        "avg_experience_years": _r(stats.mean([float(o.experience_years) for o in ops if o.experience_years is not None])) if ops else None,
    }
    return {"period": f"{start} to {end}", "days": DAYS, "kpis": kpis, "coverage": coverage, "absenteeism_daily": absent_daily, "absenteeism_heat": heat_rows, "skills": skill_rows,
            "directory": directory, "top_weavers": [w["code"] for w in top[:5]], "coaching": sorted(coaching, key=lambda c: c["name"] or ""),
            "notes": ["Weaver performance is the efficiency of the looms a person ran in their shifts. Looms, styles and conditions differ.",
                      "No pay or appraisal data is held here.", "Coaching suggestions appear only where a weaver's stops are clearly above what any weaver gets on the same looms (at least 1.3x, p < 0.001, at least 25 stops)."]}

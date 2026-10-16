"""Group-by views over the same aggregates: by loom, style, beam, shift, day (and cause / defect type)."""
from __future__ import annotations

from typing import Callable, Dict, List

from app.weaving.analytics import calc
from app.weaving.analytics.context import AnalysisContext

PRODUCTION_DIMS = ("loom", "style", "beam", "shift", "day", "loom_type")
STOP_DIMS = ("loom", "style", "beam", "shift", "day", "cause", "category")
QUALITY_DIMS = ("loom", "style", "beam", "shift", "day", "defect_type")


def _r(x, n=1):
    return None if x is None else round(x, n)


def _dim(ctx: AnalysisContext, dim: str) -> tuple[Callable, Callable]:
    """(key function over any fact row, label function for a key)."""
    refs = ctx.refs
    if dim == "loom":
        return (lambda r: r.loom_id), refs.loom_code
    if dim == "style":
        return (lambda r: r.style_id), refs.style_code
    if dim == "beam":
        return (lambda r: r.beam_id), refs.beam_no
    if dim == "shift":
        return (lambda r: r.shift_id), refs.shift_name
    if dim == "day":
        return (lambda r: r.shift_date), lambda d: d.isoformat()
    raise ValueError(dim)


def production_breakdown(ctx: AnalysisContext, group_by: str) -> List[dict]:
    refs = ctx.refs
    rows = ctx.prod_between(ctx.window.start_date, ctx.window.end_date)
    if group_by == "loom_type":
        key, label = (lambda r: refs.looms[r.loom_id].loom_type), (lambda k: k)
    else:
        key, label = _dim(ctx, group_by)
    out = []
    for k, a in calc.roll_production(rows, key).items():
        out.append({
            "key": str(label(k)), "scheduled_hours": _r(a.scheduled_h), "running_hours": _r(a.running_h), "utilization_pct": _r(a.utilization_pct), "efficiency_pct": _r(a.efficiency_pct),
            "fabric_m": _r(a.meters, 0), "target_m": _r(a.target_meters, 0), "achievement_pct": _r(a.achievement_pct), "picks": round(a.picks),
            "readings": a.readings, "readings_without_picks": a.no_picks,
        })
    return sorted(out, key=lambda x: x["key"])


def stoppage_breakdown(ctx: AnalysisContext, group_by: str) -> List[dict]:
    refs = ctx.refs
    w = ctx.window
    stops = ctx.stops_window
    prod = ctx.prod_between(w.start_date, w.end_date)
    params = calc.loom_impact_params(prod, refs)
    if group_by == "cause":
        key, label, pkey = (lambda r: r.reason_id), (lambda i: refs.reasons[i].name), None
    elif group_by == "category":
        key, label, pkey = (lambda r: refs.reasons[r.reason_id].category), (lambda k: k), None
    else:
        key, label = _dim(ctx, group_by)
        pkey = key
    picks = calc.roll_production(prod, pkey) if pkey else {}
    total_picks = calc.total_production(prod).picks
    groups: Dict[object, List] = {}
    for r in stops:
        groups.setdefault(key(r), []).append(r)
    out = []
    for k, rws in groups.items():
        a = calc.total_stops(rws)
        imp = calc.downtime_impact(rws, params)
        pk = picks[k].picks if (pkey and k in picks) else total_picks
        out.append({
            "key": str(label(k)), "stops": a.events, "stops_per_100k_picks": _r(a.per_100k_picks(pk), 2), "downtime_min": _r(a.downtime_min, 0), "unplanned_downtime_min": _r(a.unplanned_downtime_min, 0),
            "avg_stop_min": _r(a.avg_duration_min, 2), "open_stops": a.open_events, "est_lost_m": _r(imp.lost_m, 0), "est_lost_lakhs": _r(imp.lost_lakhs, 3),
        })
    return sorted(out, key=lambda x: -(x["downtime_min"] or 0))


def quality_breakdown(ctx: AnalysisContext, group_by: str) -> List[dict]:
    refs = ctx.refs
    w = ctx.window
    insp, defs = ctx.insp_between(w.start_date, w.end_date)
    prod_m = None
    if group_by == "defect_type":
        total = calc.total_quality(insp, defs)
        by_t: Dict[int, int] = {}
        for d in defs:
            by_t[d.defect_type_id] = by_t.get(d.defect_type_id, 0) + d.defects
        return sorted([{"key": refs.defect_types[t].name, "defects": c, "defects_per_100m": _r(c / total.length_m * 100, 2) if total.length_m else None,
                        "share_pct": _r(c / max(sum(by_t.values()), 1) * 100)} for t, c in by_t.items()], key=lambda x: -x["defects"])
    key, label = _dim(ctx, group_by)
    prod_m = calc.roll_production(ctx.prod_between(w.start_date, w.end_date), key)
    out = []
    for k, q in calc.roll_quality(insp, defs, key).items():
        produced = prod_m[k].meters if k in prod_m else None
        out.append({
            "key": str(label(k)), "rolls": q.rolls, "inspected_m": _r(q.length_m, 0), "defects": q.defects, "defects_per_100m": _r(q.defects_per_100m, 2), "points_per_100m": _r(q.points_per_100m, 2),
            "grade_a_pct": _r(q.grade_a_pct), "grade_b_pct": _r(q.grade_b_pct), "grade_c_or_reject_pct": _r(q.grade_c_pct),
            "inspection_coverage_pct": _r(q.length_m / produced * 100) if produced else None,
        })
    return sorted(out, key=lambda x: x["key"])

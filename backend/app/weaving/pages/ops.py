"""Production and Stoppages pages."""
from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from typing import Dict, List

from app.weaving.analytics import calc, facts, forecast
from app.weaving.pages import commercial
from app.weaving.pages.shared import Mill, kpi, r1


def _loss_waterfall(mill: Mill, prod_total: calc.ProdAgg, stops) -> List[dict]:
    """Scheduled loom-hours down to effective weaving hours: where the day's capacity went."""
    refs = mill.refs
    sched_h = prod_total.scheduled_h
    planned = sum(r.downtime_s for r in stops if r.is_planned) / 3600.0
    by_reason: Dict[int, float] = defaultdict(float)
    for r in stops:
        if not r.is_planned:
            by_reason[r.reason_id] += r.downtime_s / 3600.0
    unplanned = sum(by_reason.values())
    running_h = prod_total.running_h
    effective_h = (prod_total.picks / max(prod_total.capacity_picks, 1)) * (prod_total.measured_s / 3600.0) if prod_total.capacity_picks else 0.0
    # hours the loom ran but wove less than its rated speed would (slow running, with the readings that have a pick count)
    run_measured_h = prod_total.measured_running_s / 3600.0
    speed_loss = max(run_measured_h - effective_h, 0.0)
    unexplained = max(sched_h - running_h - planned - unplanned, 0.0)
    rows = [{"label": "Scheduled loom-hours", "value": round(sched_h), "kind": "total"}]
    if planned:
        rows.append({"label": "Planned stops (beam / style change, PM)", "value": -round(planned), "kind": "loss"})
    ranked = sorted(by_reason.items(), key=lambda kv: -kv[1])
    for rid, h in ranked[:5]:
        rows.append({"label": refs.reasons[rid].name, "value": -round(h), "kind": "loss"})
    rest = sum(h for _, h in ranked[5:])
    if rest:
        rows.append({"label": "Other stops", "value": -round(rest), "kind": "loss"})
    if unexplained > 1:
        rows.append({"label": "Not explained by stop records", "value": -round(unexplained), "kind": "loss"})
    rows.append({"label": "Running below rated speed", "value": -round(speed_loss), "kind": "loss"})
    rows.append({"label": "Effective weaving hours", "value": round(effective_h), "kind": "total"})
    return rows


def production(mill: Mill) -> dict:
    ctx, refs = mill.ctx, mill.refs
    w, pw = ctx.window, ctx.previous
    prod = ctx.prod_between(w.start_date, w.end_date)
    cur = calc.total_production(prod)
    prev = calc.total_production(ctx.prod_between(pw.start_date, pw.end_date))
    stops = ctx.stops_window
    sc = calc.total_stops([r for r in stops if not r.is_planned])
    sp = calc.total_stops([r for r in ctx.stops_previous if not r.is_planned])
    end = w.end_date
    series = mill.daily(end - timedelta(days=13), end)
    done = [d for d in series if d["complete"]]
    fc = forecast.forecast_daily([d["meters"] for d in done], horizon=7) if len(done) >= 10 else None
    spark = lambda key: [d[key] for d in series if d[key] is not None]

    energy_days: Dict[object, List[float]] = defaultdict(lambda: [0.0, 0.0])
    sens = [r for r in ctx.sensor_days if w.start_date <= r.shift_date <= w.end_date]
    kwh_by_loom: Dict[int, float] = defaultdict(float)
    for r in sens:
        kwh_by_loom[r.loom_id] += r.kwh
    P_loom = calc.roll_production(prod, lambda r: r.loom_id)
    total_kwh = sum(kwh_by_loom.values())
    cov = sum(r.with_sensors for r in sens) / max(sum(r.readings for r in sens), 1)
    kwh100 = total_kwh / cur.meters * 100 if cur.meters and total_kwh else None
    pkwh = sum(r.kwh for r in ctx.sensor_days if pw.start_date <= r.shift_date <= pw.end_date)
    pkwh100 = pkwh / prev.meters * 100 if prev.meters and pkwh else None
    e_daily = []
    P_day = calc.roll_production(ctx.prod_between(end - timedelta(days=13), end), lambda r: r.shift_date)
    kwh_day: Dict[object, float] = defaultdict(float)
    for r in ctx.sensor_days:
        kwh_day[r.shift_date] += r.kwh
    for d, a in sorted(P_day.items()):
        if a.meters > 0 and kwh_day.get(d):
            e_daily.append(r1(kwh_day[d] / a.meters * 100))

    # loom table
    loom_rows = []
    S_loom = calc.roll_stops([r for r in stops if not r.is_planned], lambda r: r.loom_id)
    P_ls = calc.roll_production(prod, lambda r: (r.loom_id, r.style_id))
    dom = {}
    for (lid, sid), a in P_ls.items():
        if lid not in dom or a.meters > P_ls[(lid, dom[lid])].meters:
            dom[lid] = sid
    for lid, a in P_loom.items():
        sid = dom.get(lid)
        s = S_loom.get(lid)
        loom_rows.append({"loom": refs.loom_code(lid), "type": refs.looms[lid].loom_type, "style": refs.style_code(sid), "meters": round(a.meters), "target_m": round(a.target_meters), "achievement_pct": r1(a.achievement_pct),
                          "efficiency_pct": r1(a.efficiency_pct), "utilization_pct": r1(a.utilization_pct), "stops_per_100k": r1(s.per_100k_picks(a.picks), 2) if s else None,
                          "kwh_per_100m": r1(kwh_by_loom[lid] / a.meters * 100) if kwh_by_loom.get(lid) and a.meters else None, "health": mill.health[lid]["score"] if lid in mill.health else None})
    loom_rows.sort(key=lambda r: r["loom"])
    ranked = sorted([r for r in loom_rows if r["efficiency_pct"] is not None], key=lambda r: -r["efficiency_pct"])
    # heatmap: loom x day efficiency
    hm_days = [end - timedelta(days=i) for i in range(13, -1, -1)]
    D = calc.roll_production(ctx.prod_between(hm_days[0], end), lambda r: (r.loom_id, r.shift_date))
    heat = []
    for lid in sorted(refs.looms, key=lambda i: refs.loom_code(i)):
        vals = []
        for d in hm_days:
            a = D.get((lid, d))
            vals.append(r1(a.efficiency_pct) if a and a.measured_s >= 6 * 3600 else None)
        if any(v is not None for v in vals):
            heat.append({"loom": refs.loom_code(lid), "type": refs.looms[lid].loom_type, "values": vals})
    shifts = calc.roll_production(prod, lambda r: r.shift_id)
    styles = calc.roll_production(prod, lambda r: r.style_id)
    types = calc.roll_production(prod, lambda r: refs.looms[r.loom_id].loom_type)
    insp, defs = ctx.insp_between(w.start_date, w.end_date)
    shift_q = calc.roll_quality(insp, defs, lambda r: r.shift_id)
    return {
        "as_of": mill.now.isoformat(), "period": w.label, "complete": w.complete,
        "kpis": [kpi("Output", cur.meters, "m", (prev.meters * cur.measured_s / prev.measured_s) if prev.measured_s else None, "up", spark("meters"), f"{cur.achievement_pct or 0:.1f}% of target", decimals=0),
                 kpi("Efficiency", cur.efficiency_pct, "%", prev.efficiency_pct, "up", spark("efficiency_pct"), "target varies by style"),
                 kpi("Utilization", cur.utilization_pct, "%", prev.utilization_pct, "up", spark("utilization_pct")),
                 kpi("Stops per 100k picks", sc.per_100k_picks(cur.picks), "", sp.per_100k_picks(prev.picks), "down", spark("stops_per_100k"), decimals=2),
                 kpi("Energy per 100 m", kwh100, "kWh", pkwh100, "down", e_daily, f"{cov * 100:.0f}% of readings have power data" if cov else "no power data"),
                 kpi("Downtime", sc.unplanned_downtime_min / 60, "h", sp.unplanned_downtime_min / 60, "down", [d["downtime_min"] / 60 for d in series], "unplanned, all looms")],
        "trend": series, "forecast": fc.as_dict() if fc else None,
        "waterfall": _loss_waterfall(mill, cur, stops),
        "shifts": [{"shift": refs.shift_name(sid), "meters": round(a.meters), "target_m": round(a.target_meters), "efficiency_pct": r1(a.efficiency_pct), "utilization_pct": r1(a.utilization_pct), "grade_a_pct": r1(shift_q[sid].grade_a_pct) if sid in shift_q else None}
                   for sid, a in sorted(shifts.items(), key=lambda kv: refs.shifts[kv[0]].sort_order)],
        "loom_types": [{"type": t, "looms": sum(1 for l in refs.looms.values() if l.loom_type == t), "meters": round(a.meters), "efficiency_pct": r1(a.efficiency_pct), "utilization_pct": r1(a.utilization_pct)} for t, a in sorted(types.items())],
        "styles": [{"style": refs.style_code(sid), "fabric": refs.styles[sid].fabric_name if sid in refs.styles else "", "meters": round(a.meters), "target_m": round(a.target_meters), "efficiency_pct": r1(a.efficiency_pct),
                    "target_efficiency_pct": float(refs.styles[sid].target_efficiency_pct) if sid in refs.styles else None, "achievement_pct": r1(a.achievement_pct)} for sid, a in sorted(styles.items(), key=lambda kv: -kv[1].meters)],
        "leaders": ranked[:5], "laggards": ranked[-5:][::-1], "looms": loom_rows, "heatmap": {"days": [f"{d:%d %b}" for d in hm_days], "rows": heat},
    }


def stoppages(mill: Mill) -> dict:
    ctx, refs = mill.ctx, mill.refs
    w = ctx.window
    stops = [r for r in ctx.stops_window if not r.is_planned]
    all_stops = ctx.stops_window
    prod = ctx.prod_between(w.start_date, w.end_date)
    P = calc.total_production(prod)
    cur = calc.total_stops(stops)
    prev = calc.total_stops([r for r in ctx.stops_previous if not r.is_planned])
    pprev = calc.total_production(ctx.prod_between(ctx.previous.start_date, ctx.previous.end_date))
    end = w.end_date
    series = mill.daily(end - timedelta(days=13), end)
    # Pareto of downtime by cause
    by_reason = calc.roll_stops(all_stops, lambda r: r.reason_id)
    total = sum(a.downtime_s for a in by_reason.values()) or 1.0
    params = calc.loom_impact_params(prod, refs)
    pareto, cum = [], 0.0
    for rid, a in sorted(by_reason.items(), key=lambda kv: -kv[1].downtime_s):
        if a.downtime_s <= 0:
            continue
        cum += a.downtime_s / total * 100
        imp = calc.downtime_impact([r for r in all_stops if r.reason_id == rid], params, include_planned=True)
        reason = refs.reasons[rid]
        pareto.append({"cause": reason.name, "category": reason.category, "planned": reason.is_planned, "stops": a.events, "downtime_min": round(a.downtime_min), "share_pct": r1(a.downtime_s / total * 100), "cumulative_pct": r1(cum),
                       "avg_min": r1(a.avg_duration_min, 1), "per_100k": r1(a.per_100k_picks(P.picks), 2) if not reason.is_planned else None, "est_lost_m": round(imp.lost_m), "est_lost_lakhs": mill.lakhs(imp.lost_lakhs), "hint": reason.diagnostic_hint})
    # downtime per day by category (stacked)
    cats = sorted({refs.reasons[r.reason_id].category for r in ctx.stops_between(end - timedelta(days=13), end) if not r.is_planned})
    daily_cat = []
    rows14 = [r for r in ctx.stops_between(end - timedelta(days=13), end) if not r.is_planned]
    by_day_cat = calc.roll_stops(rows14, lambda r: (r.shift_date, refs.reasons[r.reason_id].category))
    for i in range(13, -1, -1):
        d = end - timedelta(days=i)
        row = {"label": f"{d:%d %b}"}
        for c in cats:
            a = by_day_cat.get((d, c))
            row[c] = round(a.downtime_min) if a else 0
        daily_cat.append(row)
    # when do stops happen
    heat = facts.load_stop_heat(mill.db, ctx.lens_window.start_at, ctx.lens_window.end_at, ctx.cal.tz.key)
    grid = [[0] * 24 for _ in range(7)]
    for dow, hour, n, _ in heat:
        grid[dow][hour] += n
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    # loom x cause matrix
    cats_top = [p["category"] for p in sorted({p["category"]: p for p in pareto if not p["planned"]}.values(), key=lambda p: -p["downtime_min"])][:6]
    M = calc.roll_stops(stops, lambda r: (r.loom_id, refs.reasons[r.reason_id].category))
    by_loom = calc.roll_stops(stops, lambda r: r.loom_id)
    top_looms = [l for l, _ in sorted(by_loom.items(), key=lambda kv: -kv[1].downtime_s)[:10]]
    matrix = [{"loom": refs.loom_code(l), "total_min": round(by_loom[l].downtime_min), "cells": {c: round(M[(l, c)].downtime_min) if (l, c) in M else 0 for c in cats_top}} for l in top_looms]
    # by shift and cause
    SC = calc.roll_stops(stops, lambda r: (r.shift_id, refs.reasons[r.reason_id].category))
    shift_rows = [{"shift": refs.shift_name(sid), "cells": {c: round(SC[(sid, c)].downtime_min) if (sid, c) in SC else 0 for c in cats_top}} for sid in sorted(refs.shifts, key=lambda i: refs.shifts[i].sort_order)]
    from app.weaving.pages.overview import _stopped_now
    repeat = [f for f in mill.for_me(mill.findings) if f.kind == "recurring_stop"]
    return {"as_of": mill.now.isoformat(), "period": w.label,
            "kpis": [kpi("Unplanned stops", float(cur.events), "", float(prev.events) * (P.measured_s / pprev.measured_s) if pprev.measured_s else None, "down", [], decimals=0),
                     kpi("Per 100k picks", cur.per_100k_picks(P.picks), "", prev.per_100k_picks(pprev.picks), "down", [d["stops_per_100k"] for d in series if d["stops_per_100k"] is not None], decimals=2),
                     kpi("Average stop", cur.avg_duration_min, "min", prev.avg_duration_min, "down", [], "unplanned, finished stops"),
                     kpi("Downtime", cur.unplanned_downtime_min / 60, "h", prev.unplanned_downtime_min / 60, "down", [d["downtime_min"] / 60 for d in series]),
                     kpi("Open now", float(len(mill.open_stops)), "", None, "down", [], "looms stopped this minute", decimals=0, status="warn" if mill.open_stops else "ok")],
            "pareto": pareto, "daily_by_category": {"categories": cats, "rows": daily_cat}, "heatmap": {"days": weekdays, "hours": list(range(24)), "grid": grid, "window": ctx.lens_window.start_date.isoformat() + " to " + ctx.lens_window.end_date.isoformat()},
            "matrix": {"categories": cats_top, "rows": matrix}, "by_shift": {"categories": cats_top, "rows": shift_rows}, "open_now": _stopped_now(mill), "repeat": mill.finding_dicts(repeat[:6]), "trend": series,
            "notes": ["Downtime is clipped to the period; an open stop counts up to now. Planned stops (beam / style change, maintenance) appear in the Pareto but not in the stop rate."]}

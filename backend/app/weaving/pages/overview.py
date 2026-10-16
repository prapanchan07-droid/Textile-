"""Command Centre (the weaving GM) and Owner Brief."""
from __future__ import annotations

from datetime import timedelta
from typing import List, Optional

from app.core.roles import ROLE_LABELS
from app.weaving.analytics import calc, facts, forecast
from app.weaving.pages import commercial
from app.weaving.pages.shared import Mill, brief_line, kpi, r1


def _stopped_now(mill: Mill) -> List[dict]:
    refs, now = mill.refs, mill.now
    alerts_by_loom = {}
    for a in mill.alerts:
        alerts_by_loom.setdefault(a.loom_id, a)
    out = []
    for loom_id, st in sorted(mill.open_stops.items(), key=lambda kv: kv[1]["since"]):
        reason = refs.reasons[st["reason_id"]]
        a = alerts_by_loom.get(loom_id)
        out.append({"loom": refs.loom_code(loom_id), "reason": reason.name, "category": reason.category, "minutes": int((now - st["since"]).total_seconds() / 60), "planned": reason.is_planned,
                    "weaver": refs.operators[st["weaver_id"]].full_name if st["weaver_id"] in refs.operators else None, "fitter": refs.operators[st["fitter_id"]].full_name if st["fitter_id"] in refs.operators else None,
                    "hint": reason.diagnostic_hint, "watch": f"{a.title} ({a.level.lower()})" if a else None})
    return sorted(out, key=lambda x: -x["minutes"])


def _day_progress(mill: Mill) -> dict:
    ctx, refs = mill.ctx, mill.refs
    hours = facts.load_hourly(mill.db, ctx.today)
    cum_a = cum_p = 0.0
    rows = []
    for h in hours:
        cum_a += h.meters
        cum_p += h.target_m
        local = h.start.astimezone(ctx.cal.tz)
        rows.append({"hour": f"{local:%H:%M}", "shift": refs.shift_name(h.shift_id), "actual_m": round(h.meters), "plan_m": round(h.target_m), "cum_actual_m": round(cum_a), "cum_plan_m": round(cum_p),
                     "running_pct": r1(h.running_s / h.scheduled_s * 100) if h.scheduled_s else None})
    return {"day": ctx.today.isoformat(), "hours": rows, "actual_m": round(cum_a), "plan_m": round(cum_p), "achievement_pct": r1(cum_a / cum_p * 100) if cum_p else None}


def _live_counts(mill: Mill) -> dict:
    st = [mill.loom_status(i) for i in mill.refs.looms]
    return {"running": st.count("RUNNING"), "stopped": st.count("STOPPED"), "idle": st.count("IDLE"), "total": len(st)}


def _period_kpis(mill: Mill) -> dict:
    ctx = mill.ctx
    w, pw = ctx.window, ctx.previous
    cur = calc.total_production(ctx.prod_between(w.start_date, w.end_date))
    prev = calc.total_production(ctx.prod_between(pw.start_date, pw.end_date))
    sc = calc.total_stops([r for r in ctx.stops_window if not r.is_planned])
    sp = calc.total_stops([r for r in ctx.stops_previous if not r.is_planned])
    insp, defs = ctx.insp_between(w.start_date, w.end_date)
    pinsp, pdefs = ctx.insp_between(pw.start_date, pw.end_date)
    q, pq = calc.total_quality(insp, defs), calc.total_quality(pinsp, pdefs)
    return {"cur": cur, "prev": prev, "stops": sc, "pstops": sp, "q": q, "pq": pq}


def command(mill: Mill) -> dict:
    ctx, refs = mill.ctx, mill.refs
    k = _period_kpis(mill)
    cur, prev, sc, sp, q, pq = k["cur"], k["prev"], k["stops"], k["pstops"], k["q"], k["pq"]
    end = ctx.window.end_date
    series = mill.daily(end - timedelta(days=13), end)
    spark = lambda key: [d[key] for d in series if d[key] is not None]
    done_series = [d for d in series if d["complete"]]
    fc = forecast.forecast_daily([d["meters"] for d in done_series], horizon=3) if len(done_series) >= 10 else None
    live = _live_counts(mill)
    stopped = _stopped_now(mill)
    alerts = [a.as_dict() for a in mill.alerts if a.level in ("CRITICAL", "WARNING")][:6]
    top = mill.for_me(mill.findings)[:4]
    risky_orders = [o for o in mill.orders if o["risk"] in ("LATE", "AT_RISK")]
    from app.weaving.analytics import workforce
    wf = workforce.build(ctx, False)
    gaps = [c for c in wf["coverage"] if c["gap"] > 0]
    # the morning brief: what a GM should know in one minute, each line with its evidence one click away
    brief = []
    for f in top[:3]:
        brief.append(brief_line(f.severity, f.title + ". " + (f.next_steps[0] if f.next_steps else ""), f.link, "finding", f.evidence.estimated_impact.lost_lakhs if f.evidence.estimated_impact else None))
    for a in alerts[:2]:
        brief.append(brief_line("HIGH" if a.get("level") == "CRITICAL" else "MEDIUM", a["title"] + ": " + a["facts"][0], f"/weaving/machines?loom={a['loom']}", "machine"))
    for o in risky_orders[:2]:
        brief.append(brief_line("HIGH" if o["risk"] == "LATE" else "MEDIUM", f"{o['order_no']} ({o['customer']}): {o['explain']}", "/weaving/orders", "order", o["revenue_at_stake_lakhs"]))
    for c in gaps[:1]:
        brief.append(brief_line("MEDIUM", f"{c['shift']} has {c['present']} of {c['required']} {c['role'].lower()} present.", "/weaving/workforce", "people"))
    notes = []
    headline = (f"{live['running']} of {live['total']} looms running, {live['stopped']} stopped. {ctx.window.label}: efficiency {r1(cur.efficiency_pct)}%"
                f"{'' if prev.efficiency_pct is None or cur.efficiency_pct is None else f' ({cur.efficiency_pct - prev.efficiency_pct:+.1f} pts)'}, "
                f"{len([o for o in mill.orders if o['risk'] == 'LATE'])} order(s) late, {len([o for o in mill.orders if o['risk'] == 'AT_RISK'])} at risk.")
    shifts = calc.roll_production(ctx.prod_between(ctx.window.start_date, ctx.window.end_date), lambda r: r.shift_id)
    shift_q = calc.roll_quality(*ctx.insp_between(ctx.window.start_date, ctx.window.end_date), lambda r: r.shift_id)
    shift_s = calc.roll_stops([r for r in ctx.stops_window if not r.is_planned], lambda r: r.shift_id)
    return {
        "as_of": mill.now.isoformat(), "period": ctx.window.label, "headline": headline,
        "kpis": [
            kpi("Output", cur.meters, "m", (prev.meters * cur.measured_s / prev.measured_s) if prev.measured_s else None, "up", spark("meters"), f"target {cur.target_meters:,.0f} m", decimals=0),
            kpi("Efficiency", cur.efficiency_pct, "%", prev.efficiency_pct, "up", spark("efficiency_pct"), "picks inserted / rated capacity"),
            kpi("Utilization", cur.utilization_pct, "%", prev.utilization_pct, "up", spark("utilization_pct"), "running time / scheduled time"),
            kpi("Stops per 100k picks", sc.per_100k_picks(cur.picks), "", sp.per_100k_picks(prev.picks), "down", spark("stops_per_100k"), f"{sc.avg_duration_min or 0:.1f} min average", decimals=2),
            kpi("First grade", q.grade_a_pct, "%", pq.grade_a_pct, "up", [], f"{q.defects_per_100m or 0:.1f} defects per 100 m"),
            kpi("Orders at risk", float(len(risky_orders)), "", None, "down", [], f"{sum(1 for o in mill.orders if o['risk'] == 'LATE')} already late", decimals=0, status="bad" if risky_orders else "ok"),
        ],
        "live": {**live, "stopped_now": stopped}, "day_progress": _day_progress(mill),
        "trend": series, "forecast": fc.as_dict() if fc else None, "brief": brief, "alerts": alerts, "findings": mill.finding_dicts(top[:3]),
        "orders": [{**o, "revenue_at_stake_lakhs": mill.lakhs(o["revenue_at_stake_lakhs"])} for o in risky_orders[:5]],
        "staffing": wf["coverage"],
        "shifts": [{"shift": refs.shift_name(sid), "meters": round(a.meters), "target_m": round(a.target_meters), "efficiency_pct": r1(a.efficiency_pct), "utilization_pct": r1(a.utilization_pct),
                    "defects_per_100m": r1(shift_q[sid].defects_per_100m, 2) if sid in shift_q else None, "stops_per_100k": r1(shift_s[sid].per_100k_picks(a.picks), 2) if sid in shift_s else None}
                   for sid, a in sorted(shifts.items(), key=lambda kv: refs.shifts[kv[0]].sort_order)],
        "health_summary": {"at_risk": sum(1 for h in mill.health.values() if h["band"] == "AT_RISK"), "watch": sum(1 for h in mill.health.values() if h["band"] == "WATCH"), "healthy": sum(1 for h in mill.health.values() if h["band"] == "HEALTHY")},
    }


def owner(mill: Mill) -> dict:
    ctx, refs = mill.ctx, mill.refs
    w, pw = ctx.window, ctx.previous
    k = _period_kpis(mill)
    cur, prev = k["cur"], k["prev"]
    prod = ctx.prod_between(w.start_date, w.end_date)
    params = calc.loom_impact_params(prod, refs)
    loom_style = calc.roll_production(prod, lambda r: (r.loom_id, r.style_id))
    def shortfall(rows):
        miss_m = miss_l = revenue = 0.0
        for (lid, sid), a in calc.roll_production(rows, lambda r: (r.loom_id, r.style_id)).items():
            gap = max(0.0, a.target_meters - a.meters)
            miss_m += gap
            miss_l += gap * refs.contribution_per_m(sid) / 100_000.0
            if sid in refs.styles:
                revenue += a.meters * float(refs.styles[sid].rate_per_m) / 100_000.0
        return miss_m, miss_l, revenue
    miss_m, miss_l, revenue = shortfall(prod)
    pmiss_m, pmiss_l, prevenue = shortfall(ctx.prod_between(pw.start_date, pw.end_date))
    # a window still in progress is compared with the previous window at the SAME elapsed hours, not with a full day
    scale = (cur.measured_s / prev.measured_s) if (not w.complete and prev.measured_s) else 1.0
    prev_meters, prevenue, pmiss_l = prev.meters * scale, prevenue * scale, pmiss_l * scale
    # where the money went: lost contribution split by stop cause, the rest is running slower than target
    reason_rows = {}
    for r in ctx.stops_window:
        if r.is_planned:
            continue
        reason_rows.setdefault(r.reason_id, []).append(r)
    causes = []
    for rid, rows in reason_rows.items():
        imp = calc.downtime_impact(rows, params)
        causes.append((refs.reasons[rid].name, imp.lost_lakhs))
    causes.sort(key=lambda x: -x[1])
    stops_total = sum(c[1] for c in causes)
    cap = min(1.0, miss_l / stops_total) if stops_total > 0 else 0.0  # estimates overlap with the shortfall: never explain more than was lost
    waterfall = []
    if mill.money:
        potential = sum(a.target_meters * refs.contribution_per_m(sid) / 100_000.0 for (lid, sid), a in loom_style.items())
        waterfall.append({"label": "Contribution at target", "value": round(potential, 2), "kind": "total"})
        explained = 0.0
        for name, v in causes[:5]:
            waterfall.append({"label": name, "value": -round(v * cap, 2), "kind": "loss"})
            explained += v * cap
        rest = miss_l - explained
        waterfall.append({"label": "Other stops (smaller causes)", "value": -round(sum(c[1] for c in causes[5:]) * cap, 2), "kind": "loss"})
        waterfall.append({"label": "Running below target speed", "value": -round(max(rest - sum(c[1] for c in causes[5:]) * cap, 0), 2), "kind": "loss"})
        waterfall.append({"label": "Contribution achieved", "value": round(potential - miss_l, 2), "kind": "total"})
        waterfall = [x for x in waterfall if abs(x["value"]) > 0.004 or x["kind"] == "total"]
    risky_orders = [o for o in mill.orders if o["risk"] in ("LATE", "AT_RISK")]
    summary = commercial.orders_page(mill)["summary"]
    top = mill.for_me(mill.findings)
    decisions = []
    for f in top[:3]:
        decisions.append({"kind": "finding", "severity": f.severity, "title": f.title, "why": f.facts[0], "action": f.next_steps[0] if f.next_steps else "", "link": f.link, "impact_lakhs": mill.lakhs(f.evidence.estimated_impact.lost_lakhs if f.evidence.estimated_impact else None),
                          "confidence": f.confidence.level, "needs_approval": f.requires_human_approval})
    styles = commercial.style_economics(mill)
    for s in styles:
        if s["recommendation"] in ("STOP", "REPRICE"):
            decisions.append({"kind": "pricing", "severity": "HIGH" if s["recommendation"] == "STOP" else "MEDIUM", "title": f"{s['style']} {s['fabric']}: {s['recommendation'].lower()} the next order",
                              "why": f"Margin is {s['margin_pct']}% at {s['efficiency_pct']}% efficiency. {s['reason']}", "action": "Ask Sales to reprice, or move these looms to a higher-margin style.", "link": "/weaving/orders", "impact_lakhs": None, "confidence": "MEDIUM", "needs_approval": True})
    late = [o for o in mill.orders if o["risk"] == "LATE"]
    if late:
        o = late[0]
        decisions.append({"kind": "delivery", "severity": "HIGH", "title": f"{o['order_no']} for {o['customer']} will miss its date", "why": o["explain"], "action": "Open the AI Scheduler to see the plan that recovers the most orders, then approve or change it.",
                          "link": "/weaving/scheduler", "impact_lakhs": mill.lakhs(o["revenue_at_stake_lakhs"]), "confidence": "MEDIUM", "needs_approval": True})
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    decisions.sort(key=lambda d: (order[d["severity"]], -(d["impact_lakhs"] or 0)))
    daily = [d for d in mill.daily(w.end_date - timedelta(days=13), w.end_date) if d["complete"]]
    rev_series = []
    for d in daily:
        day = calc.roll_production([r for r in ctx.prod_between(w.end_date - timedelta(days=13), w.end_date) if r.shift_date.isoformat() == d["date"]], lambda r: r.style_id)
        rv = sum(a.meters * float(refs.styles[s].rate_per_m) / 100_000.0 for s, a in day.items() if s in refs.styles)
        rev_series.append({"label": d["label"], "revenue_lakhs": round(rv, 2) if mill.money else None, "efficiency_pct": d["efficiency_pct"]})
    cust = []
    for c in commercial.orders_page(mill)["customers"][:5]:
        cust.append(c)
    headline = (f"{ctx.window.label}: {cur.meters:,.0f} m woven" + (f", ₹{revenue:.1f} L of fabric value, ₹{miss_l:.2f} L of contribution lost to stops and slow running." if mill.money else ".")
                + f" {summary['LATE']} order(s) late and {summary['AT_RISK']} at risk.")
    cap = None
    try:
        from app.weaving.analytics import scheduler
        plan = scheduler.build_plan(ctx, mill.orders, mill.health_scores, mill.money)
        cap = {"free_loom_days": plan["proposed"]["free_loom_days"], "capacity_booked_pct": plan["proposed"]["capacity_booked_pct"], "horizon_days": plan["horizon_days"],
               "late_now": plan["baseline"]["late_orders"], "late_with_plan": plan["proposed"]["late_orders"], "moves": len({m_["loom"] for m_ in plan["moves"]})}
    except Exception:  # the brief must still render if the planner cannot run
        cap = None
    return {"as_of": mill.now.isoformat(), "period": ctx.window.label, "money_visible": mill.money, "headline": headline,
            "kpis": [kpi("Fabric woven", cur.meters, "m", prev_meters, "up", [d["meters"] for d in daily], decimals=0),
                     kpi("Fabric value", revenue if mill.money else None, "₹ L", prevenue if mill.money else None, "up", [r["revenue_lakhs"] for r in rev_series if r["revenue_lakhs"] is not None], decimals=1),
                     kpi("Contribution lost", miss_l if mill.money else None, "₹ L", pmiss_l if mill.money else None, "down", [], "stops and slow running", decimals=2),
                     kpi("Efficiency", cur.efficiency_pct, "%", prev.efficiency_pct, "up", [d["efficiency_pct"] for d in daily]),
                     kpi("Orders late / at risk", float(summary["LATE"] + summary["AT_RISK"]), "", None, "down", [], f"₹{summary['value_at_risk_lakhs']} L at stake" if mill.money and summary["value_at_risk_lakhs"] is not None else "", decimals=0, status="bad" if summary["LATE"] else "warn" if summary["AT_RISK"] else "ok")],
            "decisions": decisions[:5], "waterfall": waterfall, "orders_summary": summary, "orders": [{**o, "revenue_at_stake_lakhs": mill.lakhs(o["revenue_at_stake_lakhs"])} for o in risky_orders[:5]],
            "customers": cust, "styles": styles, "revenue_trend": rev_series, "capacity": cap}

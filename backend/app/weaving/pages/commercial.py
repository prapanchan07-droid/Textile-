"""Orders and money: delivery risk, customers, style economics, and the AI scheduler page."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select

from app.weaving import models as m
from app.weaving.analytics import calc, orders as orders_mod, scheduler
from app.weaving.pages.shared import Mill, r1

STYLE_PUSH_MARGIN, STYLE_REPRICE_MARGIN, STYLE_STOP_MARGIN = 22.0, 10.0, 3.0  # percent: business rules, shown to the user


def style_economics(mill: Mill) -> List[dict]:
    """Margin per style at the efficiency the looms are actually achieving (fixed cost spreads over fewer metres when efficiency is low)."""
    ctx, refs = mill.ctx, mill.refs
    w = ctx.window
    prod = ctx.prod_between(w.start_date, w.end_date)
    P = calc.roll_production(prod, lambda r: r.style_id)
    insp, defs = ctx.insp_between(w.start_date, w.end_date)
    Q = calc.roll_quality(insp, defs, lambda r: r.style_id)
    out = []
    for sid, a in P.items():
        st = refs.styles.get(sid)
        if st is None:
            continue
        rate, std, var = float(st.rate_per_m), float(st.std_cost_per_m), float(st.variable_cost_per_m)
        eff = a.efficiency_pct or 0.0
        target = float(st.target_efficiency_pct)
        eff_cost = var + (std - var) * (target / max(eff, 1.0))
        margin = (rate - eff_cost) / rate * 100 if rate else 0.0
        if margin < STYLE_STOP_MARGIN:
            rec, why = "STOP", "Margin is close to zero. Every extra metre adds little profit and ties up looms."
        elif margin < STYLE_REPRICE_MARGIN:
            rec, why = "REPRICE", "Margin is thin. Ask for a higher rate on the next order or move looms to a better style."
        elif margin >= STYLE_PUSH_MARGIN and eff >= target - 2:
            rec, why = "PUSH", "Healthy margin and the looms run at target. Take more orders for this style."
        else:
            rec, why = "HOLD", "Acceptable margin. Keep the current loom allocation."
        out.append({"style": st.style_code, "fabric": st.fabric_name, "meters": round(a.meters), "efficiency_pct": r1(eff), "target_efficiency_pct": target, "grade_a_pct": r1(Q[sid].grade_a_pct) if sid in Q else None,
                    "rate_per_m": rate if mill.money else None, "cost_per_m": round(eff_cost, 1) if mill.money else None, "margin_pct": round(margin, 1) if mill.money else None,
                    "profit_lakhs": mill.lakhs((rate - eff_cost) * a.meters / 100_000.0), "recommendation": rec if mill.money else None, "reason": why if mill.money else None})
    return sorted(out, key=lambda s: -(s["margin_pct"] or 0))


def orders_page(mill: Mill) -> dict:
    rows = mill.orders
    money = mill.money
    open_rows = [o for o in rows if o["state"] != "COMPLETED"]
    counts = {k: sum(1 for o in open_rows if o["risk"] == k) for k in ("LATE", "AT_RISK", "ON_TRACK", "UNSCHEDULED", "STALLED", "UNKNOWN")}
    at_stake = sum(o["revenue_at_stake_lakhs"] for o in open_rows if o["risk"] in ("LATE", "AT_RISK"))
    done = [o for o in rows if o["state"] == "COMPLETED"]
    on_time = sum(1 for o in done if o["slack_days"] is not None and o["slack_days"] >= 0)
    clean = []
    for o in rows:
        d = dict(o)
        if not money:
            d["rate_per_m"] = None
            d["revenue_at_stake_lakhs"] = None
        clean.append(d)
    custs = orders_mod.customer_rollup(rows)
    if not money:
        for c in custs:
            c["revenue_at_stake_lakhs"] = None
    return {"as_of": mill.now.isoformat(), "money_visible": money,
            "summary": {**counts, "open": len(open_rows), "completed": len(done), "completed_on_time": on_time, "value_at_risk_lakhs": round(at_stake, 2) if money else None,
                        "remaining_m": sum(o["remaining_m"] for o in open_rows)},
            "orders": clean, "customers": custs, "styles": style_economics(mill) if money else [],
            "notes": ["Expected completion projects each order's own pace over the last 7 complete production days. It assumes the order keeps its looms."]}


def scheduler_page(mill: Mill) -> dict:
    plan = scheduler.build_plan(mill.ctx, mill.orders, mill.health_scores, mill.money)
    latest = mill.db.scalars(select(m.WvSchedulePlan).order_by(m.WvSchedulePlan.created_at.desc()).limit(5)).all()
    plan["decisions"] = [{"id": p.id, "plan_ref": p.plan_ref, "status": p.status, "created_at": p.created_at.isoformat(), "decided_at": p.decided_at.isoformat() if p.decided_at else None,
                          "decision_note": p.decision_note, "moves": len(p.summary.get("moves", []))} for p in latest]
    plan["can_decide"] = mill.money
    return plan

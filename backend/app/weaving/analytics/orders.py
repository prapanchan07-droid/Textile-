"""
Order book analytics: progress, expected completion, and delivery risk.

Everything is measured from what the looms actually wove for each order (readings carry the order). Expected completion
uses the order's own recent daily output; the 80% range uses the day-to-day variation of that output. This is a
projection of the current pace, not a promise: it assumes the order keeps its looms and the pace of the last week.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional

from sqlalchemy import Float, and_, cast, func, select

from app.weaving import models as m
from app.weaving.analytics import stats
from app.weaving.analytics.context import AnalysisContext
from app.weaving.analytics.definitions import PICKS_PER_METRE_PER_PPI

RATE_DAYS = 7


def _daily_meters(ctx: AnalysisContext) -> Dict[int, Dict[date, float]]:
    R, S = m.WvLoomReading, m.WvStyle
    ppm = cast(S.ppi, Float) * PICKS_PER_METRE_PER_PPI
    q = (
        select(R.order_id, R.shift_date, func.sum(cast(R.picks, Float) / ppm))
        .join(S, S.id == R.style_id)
        .where(R.order_id.isnot(None), R.picks.isnot(None))
        .group_by(R.order_id, R.shift_date)
    )
    out: Dict[int, Dict[date, float]] = defaultdict(dict)
    for oid, d, mtr in ctx.db.execute(q):
        out[oid][d] = float(mtr or 0.0)
    return out


def _open_looms(ctx: AnalysisContext) -> Dict[int, List[str]]:
    A = m.WvOrderAssignment
    out: Dict[int, List[str]] = defaultdict(list)
    for oid, lid in ctx.db.execute(select(A.order_id, A.loom_id).where(A.assigned_to.is_(None))):
        out[oid].append(ctx.refs.loom_code(lid))
    return {k: sorted(v) for k, v in out.items()}


def order_progress(ctx: AnalysisContext) -> List[dict]:
    refs, today = ctx.refs, ctx.today
    daily = _daily_meters(ctx)
    looms = _open_looms(ctx)
    rows = ctx.db.execute(
        select(m.WvProductionOrder, m.WvStyle.style_code, m.WvStyle.fabric_name, m.WvCustomer.name, m.WvCustomer.code, m.WvCustomer.tier)
        .join(m.WvStyle, m.WvStyle.id == m.WvProductionOrder.style_id)
        .outerjoin(m.WvCustomer, m.WvCustomer.id == m.WvProductionOrder.customer_id)
        .where(m.WvProductionOrder.status != "CANCELLED")
    ).all()
    out: List[dict] = []
    for o, style, fabric, cust, cust_code, tier in rows:
        series = daily.get(o.id, {})
        produced = sum(series.values())
        ordered = float(o.ordered_m)
        remaining = max(0.0, ordered - produced)
        last_prod = max(series) if series else None
        assigned = looms.get(o.id, [])
        # daily pace from the last RATE_DAYS complete production days
        window = [series.get(today - timedelta(days=i)) for i in range(1, RATE_DAYS + 1)]
        window = [v for v in window if v is not None and v > 0]
        pace = stats.mean(window) if window else None
        sd = stats.stdev(window) if len(window) >= 3 else 0.0
        due = o.due_date
        rec = {
            "order_no": o.order_no, "style": style, "fabric": fabric, "customer": cust, "customer_code": cust_code, "tier": tier, "priority": o.priority,
            "ordered_m": round(ordered), "produced_m": round(produced), "remaining_m": round(remaining), "progress_pct": round(min(produced / ordered * 100, 100), 1) if ordered else 0.0,
            "due_date": due.isoformat() if due else None, "rate_per_m": float(o.rate_per_m) if o.rate_per_m is not None else None, "looms": assigned,
            "started_on": min(series).isoformat() if series else None,
        }
        if remaining <= ordered * 0.005 and produced > 0:
            rec.update(state="COMPLETED", risk="DONE", completed_on=last_prod.isoformat(), eta=None, slack_days=(due - last_prod).days if due else None, pace_m_per_day=None,
                       explain=f"Completed {last_prod:%d %b}" + (f", {(due - last_prod).days} day(s) before the due date." if due and last_prod <= due else ", after the due date." if due else "."))
        elif produced == 0 and not assigned:
            rec.update(state="QUEUED", risk="UNSCHEDULED", eta=None, slack_days=None, pace_m_per_day=None, completed_on=None,
                       explain="Booked but not on any loom yet. The AI Scheduler can propose where to run it." if due else "Booked but not scheduled.")
        elif not assigned and (last_prod is None or last_prod < today - timedelta(days=2)):
            rec.update(state="STALLED", risk="STALLED", eta=None, slack_days=None, pace_m_per_day=None, completed_on=None, explain="No looms are weaving this order and nothing was woven in the last two days.")
        else:
            if pace is None or pace <= 0:
                rec.update(state="RUNNING", risk="UNKNOWN", eta=None, slack_days=None, pace_m_per_day=None, completed_on=None, explain="Not enough recent output to project a completion date.")
            else:
                days_needed = remaining / pace
                eta = today + timedelta(days=math.ceil(days_needed))
                slow = max(pace - 1.2816 * sd, pace * 0.3)
                eta_late = today + timedelta(days=math.ceil(remaining / slow))
                eta_early = today + timedelta(days=math.ceil(remaining / (pace + 1.2816 * sd)))
                slack = (due - eta).days if due else None
                if due is None:
                    risk = "UNKNOWN"
                elif slack < 0:
                    risk = "LATE"
                elif slack <= 2 or eta_late > due:
                    risk = "AT_RISK"
                else:
                    risk = "ON_TRACK"
                why = f"At {pace:,.0f} m/day on {len(assigned)} loom(s), {remaining:,.0f} m remaining takes about {days_needed:.1f} days: expected {eta:%d %b}"
                why += f" against due {due:%d %b} ({'+' if slack and slack > 0 else ''}{slack} day(s) of slack)." if due else "."
                rec.update(state="RUNNING", risk=risk, eta=eta.isoformat(), eta_early=eta_early.isoformat(), eta_late=eta_late.isoformat(), slack_days=slack, pace_m_per_day=round(pace),
                           completed_on=None, explain=why)
        rec["revenue_at_stake_lakhs"] = round(remaining * rec["rate_per_m"] / 100_000.0, 2) if rec.get("rate_per_m") and rec["state"] != "COMPLETED" else 0.0
        out.append(rec)
    order = {"LATE": 0, "AT_RISK": 1, "STALLED": 2, "UNSCHEDULED": 3, "UNKNOWN": 4, "ON_TRACK": 5, "DONE": 6}
    return sorted(out, key=lambda r: (order.get(r["risk"], 9), r["due_date"] or "9999"))


def customer_rollup(orders: List[dict]) -> List[dict]:
    by: Dict[str, dict] = {}
    for o in orders:
        c = by.setdefault(o["customer"] or "Unknown", {"customer": o["customer"] or "Unknown", "tier": o["tier"], "orders": 0, "open_orders": 0, "ordered_m": 0, "remaining_m": 0,
                                                       "late": 0, "at_risk": 0, "completed_on_time": 0, "completed": 0, "revenue_at_stake_lakhs": 0.0})
        c["orders"] += 1
        c["ordered_m"] += o["ordered_m"]
        if o["state"] == "COMPLETED":
            c["completed"] += 1
            c["completed_on_time"] += 1 if (o["slack_days"] is not None and o["slack_days"] >= 0) else 0
        else:
            c["open_orders"] += 1
            c["remaining_m"] += o["remaining_m"]
            c["late"] += o["risk"] == "LATE"
            c["at_risk"] += o["risk"] == "AT_RISK"
            c["revenue_at_stake_lakhs"] = round(c["revenue_at_stake_lakhs"] + (o["revenue_at_stake_lakhs"] if o["risk"] in ("LATE", "AT_RISK") else 0.0), 2)
    return sorted(by.values(), key=lambda c: (-(c["late"] * 2 + c["at_risk"]), c["customer"]))

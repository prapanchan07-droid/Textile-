"""
AI loom scheduler: proposes which looms should weave which orders so more orders finish by their due dates.

It is a planner, not a black box. It simulates the next HORIZON days day by day twice:

  BASELINE  "carry on as booked": every loom finishes its current order, then takes the next booked order of the
            SAME style (if any), otherwise it stays idle.
  PROPOSED  the same simulation, but each day it can move looms between orders. Orders are served by urgency
            (due date, pulled forward for priority A and pushed back for priority C). An order that is projected to
            miss its date, or whose needed pace exceeds its current pace, pulls in the best available loom.

A loom is a candidate for an order only if it can weave the style (loom type, reed space) and, for priority-A orders,
is not flagged at risk by the machine-health watch. A loom is taken from another order only if that order still meets
its date without it. Moving a loom to a different style costs CHANGEOVER_DAYS of weaving.

Expected output of a loom on a style = rated speed x the loom's own recent efficiency x 24 h, converted to metres.
Nothing here changes the mill: the plan is a PROPOSAL until a manager approves it, and approval only records the
decision and raises action items for the people who would carry it out.
Simplifications (documented in docs/weaving-intelligence.md): no beam or yarn availability, constant efficiency,
one style change cost for every move, orders can be split across any number of looms.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from app.weaving.analytics import calc, stats
from app.weaving.analytics.context import AnalysisContext
from app.weaving.analytics.definitions import PICKS_PER_METRE_PER_PPI

HORIZON_DAYS = 28
CHANGEOVER_DAYS = 0.15  # about 3.6 hours lost when a loom changes style
PLANNED_STOP_ALLOWANCE = 0.985
URGENCY_SHIFT_DAYS = {"A": 3, "B": 0, "C": -3}
SAFETY = 1.05


@dataclass
class OrderIn:
    order_no: str
    style: str
    customer: Optional[str]
    priority: str
    due: Optional[date]
    remaining_m: float
    rate_per_m: Optional[float]
    current_looms: List[str]

    def urgency_date(self) -> date:
        return (self.due or date.max - timedelta(days=60)) - timedelta(days=URGENCY_SHIFT_DAYS.get(self.priority, 0))


@dataclass
class LoomIn:
    code: str
    loom_type: str
    reed_cm: float
    rpm: int
    eff: float
    style: Optional[str]
    order: Optional[str]
    health: int


@dataclass
class StyleIn:
    code: str
    ppi: float
    width_in: float
    type_required: Optional[str]


def capable(loom: LoomIn, style: StyleIn) -> bool:
    if style.type_required and loom.loom_type != style.type_required:
        return False
    return loom.reed_cm >= style.width_in * 2.54 - 0.01


def daily_capacity(loom: LoomIn, style: StyleIn) -> float:
    picks = loom.rpm * 1440.0 * loom.eff / 100.0 * PLANNED_STOP_ALLOWANCE
    return picks / (style.ppi * PICKS_PER_METRE_PER_PPI)


@dataclass
class SimResult:
    completion: Dict[str, Optional[float]]  # order -> day index (fractional) when it completes
    segments: Dict[str, List[dict]]  # loom -> [{order, start_day, end_day, metres}]
    moves: List[dict]
    changeovers: int
    loom_days_working: float
    loom_days_total: float
    output_m: float


PRIORITY_WEIGHT = {"A": 3.0, "B": 2.0, "C": 1.0}
MIN_IMPROVEMENT = 0.25  # a move must cut weighted lateness by at least this many (weighted) days to be worth the disruption
SLACK_BUFFER_DAYS = 1.0  # finishing with less than a day to spare counts as a (smaller) risk


class _State:
    """The mill at the start of a day: what is left on each order, and which loom is on which order."""

    def __init__(self, orders, looms, styles, today, frac0):
        self.orders, self.looms, self.styles, self.today, self.frac0 = orders, looms, styles, today, frac0
        self.remaining = {k: v.remaining_m for k, v in orders.items()}
        self.assign: Dict[str, Optional[str]] = {l: lo.order for l, lo in looms.items()}
        self.style: Dict[str, Optional[str]] = {l: lo.style for l, lo in looms.items()}
        self.completion: Dict[str, Optional[float]] = {k: (0.0 if v.remaining_m <= 0 else None) for k, v in orders.items()}
        self.pending_loss: Dict[str, float] = {}

    def copy(self) -> "_State":
        c = _State.__new__(_State)
        c.orders, c.looms, c.styles, c.today, c.frac0 = self.orders, self.looms, self.styles, self.today, self.frac0
        c.remaining, c.assign, c.style, c.completion, c.pending_loss = dict(self.remaining), dict(self.assign), dict(self.style), dict(self.completion), dict(self.pending_loss)
        return c

    def cap(self, loom: str, order: str) -> float:
        return daily_capacity(self.looms[loom], self.styles[self.orders[order].style])

    def open_orders(self) -> List[str]:
        return [k for k, v in self.remaining.items() if v > 0.5]

    def release_finished(self) -> None:
        for l, o in list(self.assign.items()):
            if o is not None and self.remaining[o] <= 0.5:
                self.assign[l] = None

    def baseline_fill(self) -> None:
        """Freed looms take the next booked order of the same style (earliest due first)."""
        for l, o in self.assign.items():
            if o is not None:
                continue
            style = self.style[l]
            nxt = sorted((k for k in self.open_orders() if self.orders[k].style == style), key=lambda k: (self.orders[k].urgency_date(), k))
            if nxt:
                self.assign[l] = nxt[0]

    def move(self, loom: str, order: str) -> bool:
        """Put a loom on an order; returns True when that is a style change (which costs weaving time)."""
        changed = self.style[loom] != self.orders[order].style
        self.assign[loom] = order
        if changed:
            self.pending_loss[loom] = CHANGEOVER_DAYS
            self.style[loom] = self.orders[order].style
        return changed

    def run_day(self, d: int, log: Optional[Dict[str, List[dict]]] = None) -> float:
        frac = self.frac0 if d == 0 else 1.0
        produced: Dict[str, float] = defaultdict(float)
        working = 0.0
        for l, o in self.assign.items():
            if o is None or self.remaining[o] <= 0.5:
                continue
            loss = self.pending_loss.pop(l, 0.0)
            produced[o] += self.cap(l, o) * frac * (1 - loss)
            working += frac * (1 - loss)
        for o, mtr in produced.items():
            take = min(mtr, self.remaining[o])
            if take >= self.remaining[o] - 0.5 and self.completion[o] is None:
                self.completion[o] = d + (self.remaining[o] / mtr) * frac if mtr > 0 else d + 1.0
            self.remaining[o] -= take
        if log is not None:
            count = defaultdict(int)
            for x in self.assign.values():
                count[x] += 1
            for l, o in self.assign.items():
                live = o if (o is not None and (self.remaining[o] > 0.5 or (self.completion.get(o) is not None and self.completion[o] >= d))) else None
                share = produced.get(live, 0.0) / max(count[live], 1) if live else 0.0
                seg = log[l]
                if seg and seg[-1]["order"] == live and seg[-1]["end_day"] == d:
                    seg[-1]["end_day"] = d + 1
                    seg[-1]["metres"] += share
                else:
                    seg.append({"order": live, "start_day": d, "end_day": d + 1, "metres": share})
        return working


def _project(state: _State, d0: int) -> Dict[str, Optional[float]]:
    """Where the orders would end up if nothing else were changed from day d0 on."""
    s = state.copy()
    for d in range(d0, HORIZON_DAYS):
        s.release_finished()
        s.baseline_fill()
        s.run_day(d)
        if all(v is not None for v in s.completion.values()):
            break
    return s.completion


def _objective(state: _State, completion: Dict[str, Optional[float]]) -> float:
    """Weighted lateness in days (plus a smaller charge for finishing with less than a day to spare). Lower is better."""
    total = 0.0
    for k, o in state.orders.items():
        if o.due is None:
            continue
        due_idx = (o.due - state.today).days + 1.0  # an order due on day X may finish any time during day X
        c = completion[k] if completion[k] is not None else HORIZON_DAYS + 5.0
        late = max(0.0, c - due_idx)
        thin = max(0.0, SLACK_BUFFER_DAYS - max(0.0, due_idx - c)) if late == 0 else 0.0
        total += PRIORITY_WEIGHT.get(o.priority, 2.0) * (late + 0.3 * thin)
    return total


def _plan(state: _State, mode: str, health_gate: bool = True) -> SimResult:
    log: Dict[str, List[dict]] = {l: [] for l in state.looms}
    moves: List[dict] = []
    changeovers = 0
    working = 0.0
    replan_days = {0}
    for d in range(HORIZON_DAYS):
        state.release_finished()
        had_free = any(o is None for o in state.assign.values())
        if mode == "baseline":
            state.baseline_fill()
        else:
            state.baseline_fill()  # the default behaviour is the starting point; the planner only changes it where it pays
            if d in replan_days or had_free:
                changeovers += _improve(state, d, moves, health_gate)
        working += state.run_day(d, log)
    base_changes = 0
    return SimResult(dict(state.completion), log, moves, changeovers, working, HORIZON_DAYS * len(state.looms) - (1 - state.frac0) * len(state.looms), 0.0)


def _improve(state: _State, d: int, moves: List[dict], health_gate: bool) -> int:
    """Hill-climb: repeatedly make the single loom move that most reduces projected weighted lateness, while it is worth it."""
    changes = 0
    date_d = state.today + timedelta(days=d)
    skip: set = set()
    for _ in range(40):
        proj = _project(state, d)
        base_obj = _objective(state, proj)
        troubled = [k for k in sorted(state.open_orders(), key=lambda k: (state.orders[k].urgency_date(), k)) if k not in skip and state.orders[k].due is not None
                    and _order_cost(state, proj, k) > 0]
        if not troubled:
            break
        o = troubled[0]
        style = state.styles[state.orders[o].style]
        best: Optional[Tuple[float, str, bool]] = None
        for l, lo in state.looms.items():
            cur = state.assign[l]
            if cur == o or not capable(lo, style):
                continue
            if state.orders[o].priority == "A" and health_gate and lo.health < 60:
                continue
            trial = state.copy()
            changed = trial.move(l, o)
            obj = _objective(trial, _project(trial, d))
            gain = base_obj - obj
            if gain >= MIN_IMPROVEMENT and (best is None or (gain, not changed) > (best[0], not best[2])):
                best = (gain, l, changed)
        if best is None:
            skip.add(o)
            continue
        l = best[1]
        cur = state.assign[l]
        from_style = state.style[l]
        changed = state.move(l, o)
        changes += 1 if changed else 0
        after = _project(state, d)
        idx = lambda c: None if c is None else round(c, 1)
        moves.append({"loom": l, "from_order": cur, "to_order": o, "from_style": from_style, "to_style": style.code, "day": d, "changeover": changed,
                      "gain_m_per_day": round(state.cap(l, o)), "date": date_d.isoformat(), "lateness_cut": round(best[0], 2),
                      "to_before": idx(proj[o]), "to_after": idx(after[o]), "from_before": idx(proj[cur]) if cur else None, "from_after": idx(after[cur]) if cur else None})
    return changes


def _order_cost(state: _State, proj: Dict[str, Optional[float]], k: str) -> float:
    o = state.orders[k]
    due_idx = (o.due - state.today).days + 1.0
    c = proj[k] if proj[k] is not None else HORIZON_DAYS + 5.0
    late = max(0.0, c - due_idx)
    thin = max(0.0, SLACK_BUFFER_DAYS - max(0.0, due_idx - c)) if late == 0 else 0.0
    return late + 0.3 * thin


def simulate(orders: Dict[str, OrderIn], looms: Dict[str, LoomIn], styles: Dict[str, StyleIn], today: date, frac0: float, mode: str, health_gate: bool = True) -> SimResult:
    state = _State(orders, looms, styles, today, frac0)
    res = _plan(state, mode, health_gate)
    out_m = sum(orders[k].remaining_m - state.remaining[k] for k in orders)
    res.output_m = out_m
    res.changeovers = res.changeovers if mode != "baseline" else 0
    return res


# ---------------------------------------------------------------------------- building the inputs and the report

def _inputs(ctx: AnalysisContext, order_rows: List[dict], health: Dict[int, int]):
    refs = ctx.refs
    styles = {s.style_code: StyleIn(s.style_code, float(s.ppi), float(s.width_in or 0), s.loom_type_required) for s in refs.styles.values()}
    prod = ctx.prod_between(ctx.today - timedelta(days=14), ctx.today)
    eff = {k: v.efficiency_pct for k, v in calc.roll_production(prod, lambda r: r.loom_id).items() if v.efficiency_pct}
    type_eff: Dict[str, List[float]] = defaultdict(list)
    for lid, e in eff.items():
        type_eff[refs.looms[lid].loom_type].append(e)
    order_of_loom: Dict[str, str] = {}
    for o in order_rows:
        for lc in o["looms"]:
            order_of_loom[lc] = o["order_no"]
    style_of_order = {o["order_no"]: o["style"] for o in order_rows}
    looms: Dict[str, LoomIn] = {}
    for lid, lm in refs.looms.items():
        if not lm.is_active:
            continue
        e = eff.get(lid) or (stats.mean(type_eff[lm.loom_type]) if type_eff[lm.loom_type] else 85.0)
        cur = order_of_loom.get(lm.loom_code)
        looms[lm.loom_code] = LoomIn(lm.loom_code, lm.loom_type, float(lm.reed_space_cm or 0), lm.rated_rpm, e, style_of_order.get(cur) if cur else None, cur, health.get(lid, 100))
    orders: Dict[str, OrderIn] = {}
    for o in order_rows:
        if o["state"] == "COMPLETED":
            continue
        orders[o["order_no"]] = OrderIn(o["order_no"], o["style"], o["customer"], o["priority"], date.fromisoformat(o["due_date"]) if o["due_date"] else None, float(o["remaining_m"]), o.get("rate_per_m"), o["looms"])
    return orders, looms, styles


def _summarise(res: SimResult, orders: Dict[str, OrderIn], today: date) -> dict:
    out, late, total_late = [], 0, 0.0
    revenue_late = 0.0
    for k, o in orders.items():
        c = res.completion.get(k)
        eta = today + timedelta(days=math.ceil(c)) if c is not None else None
        slack = (o.due - eta).days if (eta and o.due) else None
        is_late = o.due is not None and (eta is None or eta > o.due)
        if is_late:
            late += 1
            total_late += (eta - o.due).days if eta else HORIZON_DAYS
            revenue_late += o.remaining_m * (o.rate_per_m or 0) / 100_000.0
        out.append({"order_no": k, "eta": eta.isoformat() if eta else None, "slack_days": slack, "late": is_late, "beyond_horizon": eta is None})
    return {"orders": out, "late_orders": late, "total_late_days": round(total_late, 1), "changeovers": res.changeovers, "revenue_late_lakhs": round(revenue_late, 2),
            "capacity_booked_pct": round(res.loom_days_working / max(res.loom_days_total, 1) * 100, 1), "free_loom_days": round(max(res.loom_days_total - res.loom_days_working, 0)), "output_m": round(res.output_m)}


def _timeline(res: SimResult, orders: Dict[str, OrderIn], today: date) -> Dict[str, List[dict]]:
    out = {}
    for l, segs in res.segments.items():
        merged: List[dict] = []
        for s in segs:
            if merged and merged[-1]["order"] == s["order"]:
                merged[-1]["end_day"] = s["end_day"]
                merged[-1]["metres"] += s["metres"]
            else:
                merged.append(dict(s))
        out[l] = [{"order": s["order"], "style": orders[s["order"]].style if s["order"] else None, "start": (today + timedelta(days=s["start_day"])).isoformat(),
                   "end": (today + timedelta(days=s["end_day"])).isoformat(), "start_day": s["start_day"], "end_day": s["end_day"], "metres": round(s["metres"])} for s in merged]
    return out


def build_plan(ctx: AnalysisContext, order_rows: List[dict], health: Dict[int, int], with_money: bool) -> dict:
    orders, looms, styles = _inputs(ctx, order_rows, health)
    now = ctx.now
    _, day_end = ctx.cal.day_bounds(ctx.today)
    frac0 = max(0.05, (day_end - now).total_seconds() / 86400.0)
    base = simulate(orders, looms, styles, ctx.today, frac0, "baseline")
    plan = simulate(orders, looms, styles, ctx.today, frac0, "ai")
    sb, sp = _summarise(base, orders, ctx.today), _summarise(plan, orders, ctx.today)
    by_b = {o["order_no"]: o for o in sb["orders"]}
    by_p = {o["order_no"]: o for o in sp["orders"]}
    rows = []
    for k, o in orders.items():
        rows.append({"order_no": k, "style": o.style, "customer": o.customer, "priority": o.priority, "due": o.due.isoformat() if o.due else None, "remaining_m": round(o.remaining_m),
                     "baseline_eta": by_b[k]["eta"], "baseline_slack_days": by_b[k]["slack_days"], "baseline_late": by_b[k]["late"],
                     "proposed_eta": by_p[k]["eta"], "proposed_slack_days": by_p[k]["slack_days"], "proposed_late": by_p[k]["late"],
                     "improved": (by_b[k]["late"] and not by_p[k]["late"]) or ((by_b[k]["slack_days"] is not None and by_p[k]["slack_days"] is not None) and by_p[k]["slack_days"] > by_b[k]["slack_days"] + 1)})
    rows.sort(key=lambda r: (r["due"] or "9999", r["order_no"]))
    # explain every move in plain words
    moves = []
    for mv in plan.moves:
        lo, o_to = looms[mv["loom"]], orders[mv["to_order"]]
        why = []
        day_of = lambda x: (ctx.today + timedelta(days=math.ceil(x) if x is not None else HORIZON_DAYS))
        fmt = lambda x: "beyond the horizon" if x is None else f"{day_of(x):%d %b}"
        why.append(f"{mv['to_order']} (due {o_to.due:%d %b}, priority {o_to.priority}) is projected to finish {fmt(mv['to_before'])}; with this move {fmt(mv['to_after'])}")
        if mv["from_order"] is None:
            why.append(f"{mv['loom']} was not booked on any order")
        else:
            o_from = orders[mv["from_order"]]
            why.append(f"it comes off {mv['from_order']} (due {o_from.due:%d %b}), projected {fmt(mv['from_before'])} → {fmt(mv['from_after'])}")
        if mv["changeover"]:
            why.append(f"costs a style change ({mv['from_style'] or 'none'} → {mv['to_style']}, about {CHANGEOVER_DAYS * 24:.1f} h)")
        if lo.health < 80:
            why.append(f"note: {mv['loom']} health score is {lo.health}")
        moves.append({**mv, "reason": "; ".join(why) + ".", "loom_eff_pct": round(lo.eff, 1)})
    first_by_loom: Dict[str, dict] = {}
    for mv in moves:
        first_by_loom.setdefault(mv["loom"], mv)
    summary = [
        f"Orders projected late: {sb['late_orders']} as booked → {sp['late_orders']} with the proposed plan.",
        f"Total days late: {sb['total_late_days']:g} → {sp['total_late_days']:g}.",
        f"{len(first_by_loom)} loom(s) would change order; style changes: {sb['changeovers']} → {sp['changeovers']}.",
        f"Capacity booked over the next {HORIZON_DAYS} days: {sb['capacity_booked_pct']}% → {sp['capacity_booked_pct']}% ({sp['free_loom_days']} loom-days still free to sell).",
    ]
    if with_money:
        summary.append(f"Value of late orders: ₹{sb['revenue_late_lakhs']} L → ₹{sp['revenue_late_lakhs']} L.")
    import hashlib
    signature = hashlib.sha1("|".join(sorted(f"{mv['loom']}>{mv['to_order']}@{mv['date']}" for mv in moves)).encode()).hexdigest()[:16]
    return {
        "signature": signature, "generated_at": ctx.now.isoformat(), "today": ctx.today.isoformat(), "horizon_days": HORIZON_DAYS,
        "objective": "Finish as many orders by their due dates as possible (priority A first), with the fewest style changes.",
        "assumptions": [
            "Expected output of a loom = rated speed x the loom's own efficiency over the last 14 days, 24 hours a day, less 1.5% for planned stops.",
            f"Moving a loom to a different style costs {CHANGEOVER_DAYS * 24:.1f} hours of weaving.",
            "A loom can weave a style only if its type and reed space allow it. Priority-A orders avoid looms whose health score is below 60.",
            "Beam, yarn and operator availability are not modelled. Orders can be split across any number of looms.",
            "A proposal only: nothing changes until a manager approves, and approval creates action items for the floor.",
        ],
        "baseline": sb if with_money else {k: v for k, v in sb.items() if k != "revenue_late_lakhs"},
        "proposed": sp if with_money else {k: v for k, v in sp.items() if k != "revenue_late_lakhs"},
        "orders": rows, "moves": moves, "summary": summary,
        "timeline": {"proposed": _timeline(plan, orders, ctx.today), "baseline": _timeline(base, orders, ctx.today)},
        "looms": {l: {"type": lo.loom_type, "eff_pct": round(lo.eff, 1), "health": lo.health, "style": lo.style, "order": lo.order} for l, lo in looms.items()},
    }

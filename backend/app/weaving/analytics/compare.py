"""
Comparison engine: put any set of looms, styles, shifts, loom types, beams, yarn lots, yarn suppliers or weavers side by
side on the same metrics, with the first one as the reference. Differences are tested, not just shown: a gap that is
within normal variation is labelled as such.

Also builds the RECOMMENDED comparisons: the ones worth making right now, taken from the investigation findings.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Callable, Dict, List, Optional, Tuple

from sqlalchemy import select

from app.weaving import models as m
from app.weaving.analytics import calc, stats
from app.weaving.analytics.context import AnalysisContext
from app.weaving.analytics.facts import DefectRow, InspRow, ProdRow, StopRow

MIN_RATIO = 1.25  # a difference must be at least this large (or its inverse) as well as unlikely to be chance: with thousands of stops, trivial gaps are 'significant'

TYPES = ("loom", "style", "shift", "loom_type", "beam", "yarn_lot", "supplier", "weaver")

# key, label, unit, which direction is better
METRICS = [
    ("efficiency_pct", "Efficiency", "%", "high"),
    ("utilization_pct", "Utilization", "%", "high"),
    ("meters_per_day", "Output per day", "m", "high"),
    ("stops_per_100k", "Stops per 100,000 picks", "", "low"),
    ("warp_stops_per_100k", "Warp stops per 100,000 picks", "", "low"),
    ("weft_stops_per_100k", "Weft stops per 100,000 picks", "", "low"),
    ("avg_stop_min", "Average stop length", "min", "low"),
    ("downtime_min_per_day", "Downtime per day", "min", "low"),
    ("defects_per_100m", "Defects per 100 m", "", "low"),
    ("grade_a_pct", "First grade", "%", "high"),
    ("kwh_per_100m", "Energy per 100 m", "kWh", "low"),
]
METRIC = {k: (l, u, b) for k, l, u, b in METRICS}
DEFAULT_METRICS = ["efficiency_pct", "stops_per_100k", "warp_stops_per_100k", "weft_stops_per_100k", "avg_stop_min", "defects_per_100m", "grade_a_pct"]


def _r(x, n=1):
    return None if x is None else round(x, n)


class _Keys:
    """How each fact row maps to the entity being compared."""

    def __init__(self, ctx: AnalysisContext, kind: str):
        self.ctx, self.kind, refs = ctx, kind, ctx.refs
        lots = {r.lot_no: r for r in ctx.db.scalars(select(m.WvYarnLot))}
        self.lots = lots
        self.refs = refs

        def lot_of(beam_id):
            b = refs.beams.get(beam_id) if beam_id else None
            return b.yarn_lot if b else None

        self.fn: Dict[str, Callable] = {
            "loom": lambda r: refs.loom_code(r.loom_id),
            "style": lambda r: refs.style_code(r.style_id),
            "shift": lambda r: refs.shift_name(r.shift_id),
            "loom_type": lambda r: refs.looms[r.loom_id].loom_type,
            "beam": lambda r: refs.beam_no(r.beam_id) if r.beam_id else None,
            "yarn_lot": lambda r: lot_of(r.beam_id),
            "supplier": lambda r: (lots[lot_of(r.beam_id)].supplier if lot_of(r.beam_id) in lots else None),
            "weaver": lambda r: (refs.operators[r.weaver_id].employee_code if getattr(r, "weaver_id", None) in refs.operators else None),
        }
        self.key = self.fn[kind]

    def subtitle(self, key: str) -> str:
        refs = self.refs
        if self.kind == "loom":
            lm = next((l for l in refs.looms.values() if l.loom_code == key), None)
            return f"{lm.loom_type} · {lm.make or ''} {lm.model or ''}".strip(" ·") if lm else ""
        if self.kind == "style":
            st = next((s for s in refs.styles.values() if s.style_code == key), None)
            return st.fabric_name if st else ""
        if self.kind == "yarn_lot" and key in self.lots:
            lot = self.lots[key]
            return f"{lot.supplier} · strength {lot.strength_cn_tex} cN/tex · CV {lot.cv_pct}%"
        if self.kind == "weaver":
            op = next((o for o in refs.operators.values() if o.employee_code == key), None)
            return f"{op.full_name} · {op.designation}" if op else ""
        return ""

    def label(self, key: str) -> str:
        if self.kind == "weaver":
            op = next((o for o in self.refs.operators.values() if o.employee_code == key), None)
            return op.full_name if op and op.full_name else key
        return key


def options(ctx: AnalysisContext, kind: str) -> List[dict]:
    refs = ctx.refs
    if kind == "loom":
        return [{"key": l.loom_code, "label": l.loom_code, "group": l.loom_type} for l in sorted(refs.looms.values(), key=lambda x: x.loom_code)]
    if kind == "style":
        return [{"key": s.style_code, "label": f"{s.style_code} {s.fabric_name}", "group": s.weave or ""} for s in sorted(refs.styles.values(), key=lambda x: x.style_code)]
    if kind == "shift":
        return [{"key": s.name, "label": s.name, "group": ""} for s in sorted(refs.shifts.values(), key=lambda x: x.sort_order)]
    if kind == "loom_type":
        return [{"key": t, "label": t, "group": ""} for t in sorted({l.loom_type for l in refs.looms.values()})]
    keys = _Keys(ctx, kind)
    if kind == "beam":
        return [{"key": b.beam_no, "label": b.beam_no, "group": refs.style_code(b.style_id)} for b in sorted(refs.beams.values(), key=lambda x: x.beam_no)]
    if kind == "yarn_lot":
        return [{"key": k, "label": k, "group": v.supplier or ""} for k, v in sorted(keys.lots.items())]
    if kind == "supplier":
        return [{"key": s, "label": s, "group": ""} for s in sorted({v.supplier for v in keys.lots.values() if v.supplier})]
    if kind == "weaver":
        return [{"key": o.employee_code, "label": f"{o.full_name} ({o.employee_code})", "group": o.designation or ""} for o in sorted(refs.operators.values(), key=lambda x: x.employee_code) if o.operator_role == "WEAVER"]
    return []


def compare(ctx: AnalysisContext, kind: str, keys: List[str], metrics: Optional[List[str]] = None, days: int = 14, style: Optional[str] = None) -> dict:
    if kind not in TYPES:
        raise ValueError(f"unknown comparison type {kind}")
    refs = ctx.refs
    end = ctx.window.end_date
    start = end - timedelta(days=max(3, min(days, 28)) - 1)
    metrics = [k for k in (metrics or DEFAULT_METRICS) if k in METRIC]
    K = _Keys(ctx, kind)
    style_id = next((i for i, s in refs.styles.items() if s.style_code == style), None) if style else None
    keep = (lambda r: getattr(r, "style_id", None) == style_id) if style_id is not None else (lambda r: True)
    prod = [r for r in ctx.prod_between(start, end) if keep(r)]
    stops = [r for r in ctx.stops_between(start, end) if keep(r) and not r.is_planned]
    insp, defs = ctx.insp_between(start, end)
    insp, defs = [r for r in insp if keep(r)], [r for r in defs if keep(r)]
    sensors = [r for r in ctx.sensor_days if start <= r.shift_date <= end]
    warp_ids = {i for i, r in refs.reasons.items() if r.category == "WARP"}
    weft_ids = {i for i, r in refs.reasons.items() if r.category == "WEFT"}

    P = calc.roll_production(prod, K.key)
    S = calc.roll_stops(stops, K.key)
    SW = calc.roll_stops([r for r in stops if r.reason_id in warp_ids], K.key)
    SF = calc.roll_stops([r for r in stops if r.reason_id in weft_ids], K.key)
    Q = calc.roll_quality(insp, defs, K.key)
    PD = calc.roll_production(prod, lambda r: (K.key(r), r.shift_date))  # daily
    SD = calc.roll_stops(stops, lambda r: (K.key(r), r.shift_date))
    kwh: Dict[str, float] = defaultdict(float)
    if kind in ("loom", "shift", "loom_type"):
        for r in sensors:
            k = {"loom": refs.loom_code(r.loom_id), "shift": refs.shift_name(r.shift_id), "loom_type": refs.looms[r.loom_id].loom_type}[kind]
            kwh[k] += r.kwh
    days_with = {k: len({d for (kk, d) in PD if kk == k}) or 1 for k in P}

    def metrics_of(k: str) -> dict:
        p, s, sw, sf, q = P.get(k), S.get(k), SW.get(k), SF.get(k), Q.get(k)
        out = {}
        out["efficiency_pct"] = _r(p.efficiency_pct) if p else None
        out["utilization_pct"] = _r(p.utilization_pct) if p else None
        out["meters_per_day"] = _r(p.meters / days_with[k], 0) if p else None
        picks = p.picks if p else 0
        out["stops_per_100k"] = _r(s.per_100k_picks(picks), 2) if s and p else None
        out["warp_stops_per_100k"] = _r(sw.per_100k_picks(picks), 2) if sw and p else (0.0 if p and p.picks else None)
        out["weft_stops_per_100k"] = _r(sf.per_100k_picks(picks), 2) if sf and p else (0.0 if p and p.picks else None)
        out["avg_stop_min"] = _r(s.avg_duration_min, 2) if s else None
        out["downtime_min_per_day"] = _r(s.unplanned_downtime_min / days_with[k], 1) if s else None
        out["defects_per_100m"] = _r(q.defects_per_100m, 2) if q else None
        out["grade_a_pct"] = _r(q.grade_a_pct) if q else None
        out["kwh_per_100m"] = _r(kwh[k] / p.meters * 100, 1) if k in kwh and p and p.meters > 0 else None
        return out

    chosen = [k for k in keys if k in P or k in S or k in Q]
    missing = [k for k in keys if k not in chosen]
    entities = []
    for k in chosen:
        daily_eff = sorted((d, PD[(kk, d)].efficiency_pct) for (kk, d) in PD if kk == k and PD[(kk, d)].efficiency_pct is not None)
        daily_stops = []
        for (kk, d), a in sorted(PD.items(), key=lambda kv: kv[0][1]):
            if kk == k:
                sa = SD.get((kk, d))
                daily_stops.append((d, sa.per_100k_picks(a.picks) if sa else (0.0 if a.picks else None)))
        entities.append({
            "key": k, "label": K.label(k), "subtitle": K.subtitle(k), "metrics": metrics_of(k), "vs_reference": {},
            "daily": {"efficiency_pct": [{"date": d.isoformat(), "value": _r(v)} for d, v in daily_eff],
                      "stops_per_100k": [{"date": d.isoformat(), "value": _r(v, 2)} for d, v in daily_stops if v is not None]},
            "_eff_days": [v for _, v in daily_eff],
        })
    highlights: List[str] = []
    if entities:
        ref = entities[0]
        rk = ref["key"]
        for e in entities[1:]:
            vs = {}
            k = e["key"]
            # rate comparisons: eligible stops / picks, defects / metres (exact conditional tests)
            tests = {
                "stops_per_100k": (S.get(k), S.get(rk), lambda a: a.eligible_events, P, "picks"),
                "warp_stops_per_100k": (SW.get(k), SW.get(rk), lambda a: a.eligible_events, P, "picks"),
                "weft_stops_per_100k": (SF.get(k), SF.get(rk), lambda a: a.eligible_events, P, "picks"),
            }
            for mk, (a, b, ev, exposure, _) in tests.items():
                ea = ev(a) if a else 0
                eb = ev(b) if b else 0
                pa, pb = P.get(k), P.get(rk)
                if pa and pb and pa.picks > 0 and pb.picks > 0:
                    ratio, p = stats.rate_ratio_test(ea, pa.picks, eb, pb.picks)
                    ratio_rev, p_rev = stats.rate_ratio_test(eb, pb.picks, ea, pa.picks)
                    big = ratio is not None and (ratio >= MIN_RATIO or (ratio > 0 and ratio <= 1 / MIN_RATIO))
                    vs[mk] = {"ratio": _r(ratio, 2) if ratio is not None and ratio != float("inf") else None, "p_value": min(p or 1, p_rev or 1), "direction": "higher" if (ratio or 0) > 1 else "lower",
                              "significant": min(p or 1, p_rev or 1) < 0.01 and (ea + eb) >= 10 and big, "events": [ea, eb]}
            qa, qb = Q.get(k), Q.get(rk)
            if qa and qb and qa.length_m > 0 and qb.length_m > 0:
                ratio, p = stats.rate_ratio_test(qa.defects, qa.length_m, qb.defects, qb.length_m)
                ratio_rev, p_rev = stats.rate_ratio_test(qb.defects, qb.length_m, qa.defects, qa.length_m)
                big = ratio is not None and (ratio >= MIN_RATIO or (ratio > 0 and ratio <= 1 / MIN_RATIO))
                vs["defects_per_100m"] = {"ratio": _r(ratio, 2) if ratio not in (None, float("inf")) else None, "p_value": min(p or 1, p_rev or 1), "direction": "higher" if (ratio or 0) > 1 else "lower",
                                          "significant": min(p or 1, p_rev or 1) < 0.01 and (qa.defects + qb.defects) >= 15 and big, "events": [qa.defects, qb.defects]}
            if len(e["_eff_days"]) >= 5 and len(ref["_eff_days"]) >= 5:
                diff = stats.mean(e["_eff_days"]) - stats.mean(ref["_eff_days"])
                se = ((stats.stdev(e["_eff_days"]) ** 2 / len(e["_eff_days"])) + (stats.stdev(ref["_eff_days"]) ** 2 / len(ref["_eff_days"]))) ** 0.5 or 1e-9
                t = diff / se
                vs["efficiency_pct"] = {"diff": _r(diff), "t": _r(t, 2), "p_value": 2 * stats.normal_sf(abs(t)), "direction": "higher" if diff > 0 else "lower", "significant": abs(t) >= 3 and abs(diff) >= 1.0}
            e["vs_reference"] = vs
            label = METRIC
            for mk, v in vs.items():
                if not v["significant"] or mk not in metrics:
                    continue
                better = METRIC[mk][2]
                good = (v["direction"] == "higher") == (better == "high")
                if mk == "efficiency_pct":
                    highlights.append(f"{e['label']} runs {abs(v['diff']):.1f} points {'higher' if v['direction'] == 'higher' else 'lower'} efficiency than {ref['label']} (t = {v['t']}); {'better' if good else 'worse'}.")
                else:
                    r = v["ratio"]
                    txt = f"{r:.1f}×" if r and r >= 1 else (f"{1 / r:.1f}× lower" if r else "a different")
                    highlights.append(f"{e['label']} has {txt} the {METRIC[mk][0].lower()} of {ref['label']} ({v['events'][0]} vs {v['events'][1]} events, p = {v['p_value']:.2g}); {'better' if good else 'worse'}.")
        if len(entities) > 1 and not highlights:
            highlights.append("No difference between these is larger than normal day-to-day variation on the selected metrics.")
    for e in entities:
        e.pop("_eff_days", None)
    # radar: 100 = best among the chosen entities on that metric
    radar = []
    for mk in metrics:
        vals = [e["metrics"][mk] for e in entities if e["metrics"].get(mk) is not None]
        if len(vals) < 2:
            continue
        lo, hi = min(vals), max(vals)
        row = {"metric": METRIC[mk][0], "key": mk}
        for e in entities:
            v = e["metrics"].get(mk)
            if v is None:
                row[e["key"]] = None
            elif hi == lo:
                row[e["key"]] = 100.0
            else:
                score = (v - lo) / (hi - lo) if METRIC[mk][2] == "high" else (hi - v) / (hi - lo)
                row[e["key"]] = round(30 + 70 * score, 1)  # keep the worst away from the centre so the shape stays readable
        radar.append(row)
    return {"type": kind, "period": f"{start} to {end}", "days": (end - start).days + 1, "style_filter": style, "metrics": [{"key": k, "label": METRIC[k][0], "unit": METRIC[k][1], "better": METRIC[k][2]} for k in metrics],
            "reference": entities[0]["key"] if entities else None, "entities": entities, "highlights": highlights, "radar": radar, "not_found": missing,
            "notes": ["The first selection is the reference; differences are tested against it.", "Energy per 100 m is available for looms, shifts and loom types only.",
                      "Comparing people is sensitive: loom, style and shift conditions differ, so treat gaps as a prompt to look, not a verdict."]}


# ---------------------------------------------------------------------------- recommended comparisons

def recommended(ctx: AnalysisContext, findings: list) -> List[dict]:
    refs = ctx.refs
    out: List[dict] = []
    by_type_style: Dict[Tuple[str, str], List[str]] = defaultdict(list)
    for r in ctx.prod_between(ctx.lens_start, ctx.lens_end):
        pass
    meters = calc.roll_production(ctx.prod_between(ctx.lens_start, ctx.lens_end), lambda r: (r.loom_id, r.style_id))
    style_looms: Dict[str, List[Tuple[float, str]]] = defaultdict(list)
    for (lid, sid), a in meters.items():
        style_looms[refs.style_code(sid)].append((a.meters, refs.loom_code(lid)))
    for f in findings:
        if f.kind == "loom_decline":
            loom, style = f.evidence.scope["loom"], f.evidence.scope.get("style")
            peers = [c for _, c in sorted(style_looms.get(style, []), reverse=True) if c != loom][:3]
            out.append({"id": f.key, "title": f"{loom} against its {style} peers", "why": f"{f.title}. Compare it with looms weaving the same style to see which numbers moved.", "type": "loom", "keys": [peers[0], loom] + peers[1:] if peers else [loom],
                        "style": None, "metrics": ["efficiency_pct", "stops_per_100k", "warp_stops_per_100k", "weft_stops_per_100k", "avg_stop_min"], "source": "finding"})
        elif f.kind == "recurring_stop":
            loom = f.evidence.scope["loom"]
            lm = next((l for l in refs.looms.values() if l.loom_code == loom), None)
            peers = [l.loom_code for l in sorted(refs.looms.values(), key=lambda x: x.loom_code) if lm and l.loom_type == lm.loom_type and l.loom_code != loom][:3]
            out.append({"id": f.key, "title": f"{loom} against other {lm.loom_type if lm else ''} looms", "why": f.title + ". Is it the loom, or the type?", "type": "loom", "keys": [peers[0], loom] + peers[1:] if peers else [loom],
                        "style": None, "metrics": ["efficiency_pct", "stops_per_100k", "avg_stop_min", "downtime_min_per_day"], "source": "finding"})
        elif f.kind == "beam_warp_excess":
            style = f.evidence.scope["style"]
            lots = [l.strip() for l in f.evidence.scope.get("yarn_lots", "").split(",") if l.strip()]
            others = sorted({b.yarn_lot for b in refs.beams.values() if refs.style_code(b.style_id) == style and b.yarn_lot and b.yarn_lot not in lots})[-3:]
            out.append({"id": f.key, "title": f"Yarn lot {', '.join(lots)} against other {style} lots", "why": f.title + ". Compare breaks, efficiency and the lot's incoming yarn tests.", "type": "yarn_lot", "keys": others[-1:] + lots + others[:-1],
                        "style": None, "metrics": ["warp_stops_per_100k", "efficiency_pct", "stops_per_100k", "avg_stop_min"], "source": "finding"})
        elif f.kind == "shift_defect_shift":
            style = f.evidence.scope["style"]
            out.append({"id": f.key, "title": f"Shifts on {style}", "why": f.title + ". Same style, different shifts: where do the defects come from?", "type": "shift", "keys": [s.name for s in sorted(refs.shifts.values(), key=lambda x: x.sort_order)],
                        "style": style, "metrics": ["defects_per_100m", "grade_a_pct", "efficiency_pct", "stops_per_100k"], "source": "finding"})
    # always-useful comparisons
    out.append({"id": "type", "title": "Airjet against Sulzer", "why": "Which loom type earns its place: efficiency, stops and energy side by side.", "type": "loom_type", "keys": ["Airjet", "Sulzer"], "style": None,
                "metrics": ["efficiency_pct", "utilization_pct", "stops_per_100k", "avg_stop_min", "kwh_per_100m", "grade_a_pct"], "source": "standard"})
    out.append({"id": "shifts", "title": "Shift I against II against III", "why": "Same floor, different crews and conditions.", "type": "shift", "keys": [s.name for s in sorted(refs.shifts.values(), key=lambda x: x.sort_order)], "style": None,
                "metrics": ["efficiency_pct", "stops_per_100k", "avg_stop_min", "defects_per_100m", "kwh_per_100m"], "source": "standard"})
    out.append({"id": "suppliers", "title": "Yarn suppliers", "why": "Do warp breaks and efficiency differ by who supplied the yarn?", "type": "supplier", "keys": sorted({l.supplier for l in ctx.db.scalars(select(m.WvYarnLot)) if l.supplier}), "style": None,
                "metrics": ["warp_stops_per_100k", "stops_per_100k", "efficiency_pct", "defects_per_100m"], "source": "standard"})
    eff = calc.roll_production(ctx.prod_between(ctx.lens_start, ctx.lens_end), lambda r: r.loom_id)
    ranked = sorted(((a.efficiency_pct, refs.loom_code(i)) for i, a in eff.items() if a.efficiency_pct), reverse=True)
    if len(ranked) >= 6:
        out.append({"id": "bestworst", "title": "Best three against worst three looms", "why": "What do the leaders do differently from the laggards?", "type": "loom", "keys": [c for _, c in ranked[:3]] + [c for _, c in ranked[-3:]], "style": None,
                    "metrics": ["efficiency_pct", "utilization_pct", "stops_per_100k", "avg_stop_min", "kwh_per_100m"], "source": "standard"})
    seen, uniq = set(), []
    for r in out:
        if r["id"] not in seen:
            seen.add(r["id"])
            uniq.append(r)
    return uniq

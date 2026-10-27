"""
Production-loss findings: where output is being lost, with the evidence for each.

Each finding says what was observed, over which period, against which comparison, how it was computed
(`basis`: CALCULATED / STATISTICAL / MODELED) and what to check next. The sources record stop counts but not
stop causes, durations by cause (except the machine exports) or operator-entered reasons, so findings never
name a root cause; they point at where to look and what data would settle it.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.mill.analytics import metrics as M
from app.mill.analytics.records import Filters, by, cohort_key, load

MIN_COHORT = 3


def _loom_stats(rows: List[dict]) -> Dict[int, dict]:
    out = {}
    for (loom_id,), lr in by(rows, "loom_id").items():
        agg = M.aggregate(lr)
        out[loom_id] = {"loom_id": loom_id, "loom_code": lr[0]["loom_code"], "category": lr[0]["category"],
                        "cohort": cohort_key(lr), "rows": lr, **agg}
    return out


def find(db: Session, f: Filters, limit: int = 25) -> List[dict]:
    rows = load(db, f)
    if not rows:
        return []
    stats = _loom_stats(rows)
    findings: List[dict] = []
    period = {"from": f.date_from.isoformat() if f.date_from else None, "to": f.date_to.isoformat() if f.date_to else None}

    # 1. Looms below their peers (same category, width, style, source): modeled meters gap.
    cohorts: Dict[tuple, List[dict]] = {}
    for s in stats.values():
        cohorts.setdefault(s["cohort"], []).append(s)
    for key, members in cohorts.items():
        effs = [m["efficiency_pct"] for m in members if m["efficiency_pct"] is not None]
        if len(effs) < MIN_COHORT:
            continue
        med = M.median(effs)
        for m in members:
            e = m["efficiency_pct"]
            if e is None or not m["meters"] or e >= med - 3:
                continue
            gap_m = m["meters"] * (med / e - 1) if e > 0 else None
            findings.append({
                "kind": "BELOW_PEERS", "basis": "MODELED", "severity": "WARNING" if med - e < 8 else "CRITICAL",
                "title": f"{m['loom_code']} runs {med - e:.1f} pts below its peers",
                "loom_id": m["loom_id"], "loom_code": m["loom_code"], "period": period,
                "evidence": {"loom_efficiency_pct": round(e, 2), "cohort_median_efficiency_pct": round(med, 2), "cohort_size": len(effs),
                             "cohort": {"category": key[0], "width_cm": key[1], "style": key[2], "source": key[3]},
                             "loom_meters": round(m["meters"], 1), "loom_shifts": m["loom_shifts"]},
                "impact": {"meters_gap": round(gap_m, 1) if gap_m else None, "metric": "meters_gap_vs_cohort",
                           "assumption": M.BY_KEY["meters_gap_vs_cohort"].notes},
                "implication": "Lost output on a loom that peers on the same style and width run better.",
                "next_step": "Check the loom's stop pattern (warp/weft rates below), recent settings and beam; "
                             "record stop reasons for the next shifts to identify the cause.",
                "score": gap_m or 0,
            })

    # 2. High stop rates against peers (within one source; rates per 100k picks).
    for key, members in cohorts.items():
        for metric, label in (("warp_stops_cmpx", "warp"), ("weft_stops_cmpx", "weft")):
            vals = [m[metric] for m in members if m[metric] is not None]
            if len(vals) < MIN_COHORT:
                continue
            med = M.median(vals)
            for m in members:
                v = m[metric]
                if v is None or med is None or med <= 0 or v < 1.5 * med or v - med < 1:
                    continue
                findings.append({
                    "kind": f"HIGH_{label.upper()}_STOPS", "basis": "CALCULATED", "severity": "WARNING",
                    "title": f"{m['loom_code']}: {label} stops {v / med:.1f}x its peers",
                    "loom_id": m["loom_id"], "loom_code": m["loom_code"], "period": period,
                    "evidence": {f"loom_{metric}": round(v, 2), f"cohort_median_{metric}": round(med, 2), "cohort_size": len(vals),
                                 f"{label}_stops": m[f"{label}_stops"], "kilopicks": round(m["kilopicks"] or 0, 1),
                                 "unit": "stops per 100,000 picks"},
                    "impact": None,
                    "implication": f"Each {label} stop costs running time and operator attention; a rate this far above peers is usually loom- or beam-specific.",
                    "next_step": ("Inspect the warp beam, drop wires and heald/reed condition; compare with the previous beam."
                                  if label == "warp" else "Check weft supply, package sensors, nozzles/air settings and feeler signals."),
                    "score": (v - med) * (m["kilopicks"] or 0) / 100,
                })

    # 3. Looms below their own earlier performance (previous window of equal length, same source).
    if f.date_from and f.date_to:
        days = (f.date_to - f.date_from).days + 1
        prev_f = Filters(**{**f.__dict__, "date_from": f.date_from - timedelta(days=days), "date_to": f.date_from - timedelta(days=1)})
        prev = _loom_stats(load(db, prev_f))
        for loom_id, s in stats.items():
            p = prev.get(loom_id)
            if not p or s["efficiency_pct"] is None or p["efficiency_pct"] is None or p["cohort"][3] != s["cohort"][3]:
                continue
            drop = p["efficiency_pct"] - s["efficiency_pct"]
            if drop < 4 or s["loom_shifts"] < 2:
                continue
            findings.append({
                "kind": "BELOW_OWN_BASELINE", "basis": "CALCULATED", "severity": "WARNING",
                "title": f"{s['loom_code']} down {drop:.1f} pts on its previous {days} day(s)",
                "loom_id": loom_id, "loom_code": s["loom_code"], "period": period,
                "evidence": {"efficiency_pct": round(s["efficiency_pct"], 2), "previous_efficiency_pct": round(p["efficiency_pct"], 2),
                             "previous_period": {"from": prev_f.date_from.isoformat(), "to": prev_f.date_to.isoformat()},
                             "style_now": s["cohort"][2], "style_before": p["cohort"][2]},
                "impact": None,
                "implication": "A loom getting worse on itself is an early sign of a developing problem"
                               + (" (note: the style changed, which can explain it)." if s["cohort"][2] != p["cohort"][2] else "."),
                "next_step": "Open the loom page: check which shifts dropped and whether warp or weft stops rose.",
                "score": drop * s["loom_shifts"],
            })

    # 4. Shift gaps within a category (same looms, same days).
    for (cat,), cr in by(rows, "category").items():
        shifts = {s: M.eff_weighted(r) for (s,), r in by(cr, "shift").items()}
        shifts = {k: v for k, v in shifts.items() if v is not None}
        if len(shifts) < 2:
            continue
        worst, best = min(shifts, key=shifts.get), max(shifts, key=shifts.get)
        gap = shifts[best] - shifts[worst]
        if gap < 2:
            continue
        days = by(cr, "prod_date")
        worst_days = sum(1 for dr in days.values() if _worst_shift(dr) == worst)
        findings.append({
            "kind": "SHIFT_GAP", "basis": "CALCULATED", "severity": "INFO" if gap < 4 else "WARNING",
            "title": f"{cat}: shift {worst} runs {gap:.1f} pts below shift {best}",
            "loom_id": None, "loom_code": None, "category": cat, "period": period,
            "evidence": {"efficiency_by_shift": {k: round(v, 2) for k, v in sorted(shifts.items())},
                         "days_worst_shift": f"{worst_days} of {len(days)} days"},
            "impact": None,
            "implication": "A consistent gap on the same looms and styles points at people, handover or support coverage rather than machines.",
            "next_step": f"Compare staffing, fitter availability and handover practice for shift {worst}; check whether the gap is spread or concentrated on a few looms.",
            "score": gap * len(cr) / 3,
        })

    findings.sort(key=lambda x: -(x["score"] or 0))
    for x in findings:
        x["id"] = f"{x['kind']}:{x.get('loom_code') or x.get('category')}"
        x.pop("score", None)
    return findings[:limit]


def _worst_shift(day_rows: List[dict]) -> Optional[str]:
    effs = {s: M.eff_weighted(r) for (s,), r in by(day_rows, "shift").items()}
    effs = {k: v for k, v in effs.items() if v is not None}
    return min(effs, key=effs.get) if len(effs) > 1 else None


def loom_anomalies(rows: List[dict], baseline_days: int = 14, min_points: int = 6) -> List[dict]:
    """Per-shift efficiency anomalies for one loom (robust z, previous `baseline_days`, same source)."""
    out = []
    for i, r in enumerate(rows):
        if r.get("efficiency_pct") is None:
            continue
        hist = [h["efficiency_pct"] for h in rows[:i]
                if h["efficiency_pct"] is not None and h["source_kind"] == r["source_kind"]
                and 0 < (r["prod_date"] - h["prod_date"]).days <= baseline_days]
        if len(hist) < min_points:
            continue
        z = M.robust_z(r["efficiency_pct"], hist)
        if z is not None and abs(z) >= 3.5:
            out.append({"prod_date": r["prod_date"].isoformat(), "shift": r["shift"], "efficiency_pct": r["efficiency_pct"],
                        "baseline_median": round(M.median(hist), 2), "robust_z": round(z, 2), "direction": "low" if z < 0 else "high",
                        "points": len(hist), "basis": "STATISTICAL",
                        "meaning": "Unusual for this loom compared with its previous 14 days. Not a diagnosis."})
    return out


def explain_missing(category: Optional[str]) -> Optional[str]:
    if category == "SZ":
        return "The SZ (Sulzer) report has no warp/weft stop counts, so stop-based findings are not available for these looms."
    return None

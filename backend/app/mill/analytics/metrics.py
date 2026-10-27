"""
The metric layer: one definition and one implementation per KPI, used by every page, alert rule and report.

Rules that hold everywhere
  * Efficiency is aggregated as a time-weighted mean: sum(eff_i * w_i) / sum(w_i), where w_i is the record's
    monitored minutes (run + stop) when the source gives them (Toyota export), otherwise the 480-minute shift.
    With every loom on full 480-minute shifts this equals the plain mean the mill's sheets use.
  * Stop rates are per 100,000 picks ("cmpx", as Toyota and Tsudakoma report them): stops / kilopicks * 100,
    computed only over records that have both the stop count and kilopicks.
  * Sums ignore unavailable values and report how many records contributed (coverage), so a missing value
    never becomes a zero.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from app.mill.constants import SHIFT_MINUTES


@dataclass(frozen=True)
class MetricDef:
    key: str
    label: str
    meaning: str
    formula: str
    unit: str
    source_fields: str
    aggregation: str
    missing_data: str
    basis: str  # MEASURED / CALCULATED / MODELED / STATISTICAL
    notes: str = ""


DEFINITIONS: List[MetricDef] = [
    MetricDef("meters", "Production", "Woven fabric length", "sum(meters)", "m", "Meter / Product(meter) / Cloth length (meter)",
              "Sum over loom-shifts", "Loom-shifts without meters are excluded and counted in coverage", "MEASURED",
              "TY 340 cm looms: the mill report counts both panels (2x the monitoring system's counted length)."),
    MetricDef("kilopicks", "Kilopicks", "Weft insertions in thousands", "sum(kilopicks)", "kpicks", "Kilopick / Product(1000pick) / Cloth length (x100 picks) / 10",
              "Sum over loom-shifts", "Excluded and counted in coverage", "MEASURED",
              "Same panel caveat as meters for TY 340 cm looms."),
    MetricDef("efficiency_pct", "Efficiency", "Share of the shift the loom was weaving", "sum(eff_i x w_i) / sum(w_i); w = run+stop minutes if known, else 480",
              "%", "EFF % / Effi / Effic.(%) / Mill efficiency", "Time-weighted mean, never a sum or an unweighted mean of unequal periods",
              "Records without efficiency are excluded", "MEASURED",
              "Tsudakoma also reports 'Loom efficiency' (stored separately); 'Mill efficiency' is used to match the mill's report."),
    MetricDef("warp_stops", "Warp stops", "Recorded warp-stop count", "sum(warp_stops)", "stops", "Warp (times) / Warp stop times",
              "Sum", "SZ (Sulzer) report has no warp column: not available, never zero", "MEASURED"),
    MetricDef("weft_stops", "Weft stops", "Recorded weft (filling) stop count", "sum(weft_stops)", "stops", "Weft (times) / Filling stop times",
              "Sum", "Not available for SZ", "MEASURED"),
    MetricDef("warp_stops_cmpx", "Warp stop rate", "Warp stops per 100,000 picks", "sum(warp_stops) / sum(kilopicks) x 100", "stops / 100k picks",
              "warp_stops, kilopicks", "Ratio of sums over records having both", "Not computed without both fields", "CALCULATED",
              "Compare only within the same source: the mill report's doubled TY 340 cm picks halve the rate."),
    MetricDef("weft_stops_cmpx", "Weft stop rate", "Weft stops per 100,000 picks", "sum(weft_stops) / sum(kilopicks) x 100", "stops / 100k picks",
              "weft_stops, kilopicks", "Ratio of sums", "Not computed without both fields", "CALCULATED"),
    MetricDef("meters_per_loom_shift", "Output per loom-shift", "Average meters per loom per 480-minute shift", "sum(meters) / count(loom-shifts with meters)",
              "m / loom-shift", "meters", "Ratio", "Excluded when meters missing", "CALCULATED",
              "Equivalent to output per scheduled 8-hour shift; scheduled downtime is not recorded in the sources."),
    MetricDef("meters_vs_target_pct", "Production vs target", "Shortfall or excess against the configured meters-per-shift target",
              "(meters - target) / target x 100", "%", "meters, production_targets", "Per loom-shift, then summed meters vs summed target",
              "Not computed when no target is configured", "CALCULATED"),
    MetricDef("efficiency_vs_baseline", "Efficiency vs own baseline", "Points above/below the loom's median efficiency of the previous N days (same source)",
              "eff - median(eff over previous N days)", "pts", "efficiency_pct", "Per record", "Needs at least the configured number of earlier records",
              "STATISTICAL"),
    MetricDef("efficiency_robust_z", "Efficiency anomaly score", "How unusual a shift is for this loom", "(eff - median) / (1.4826 x MAD), previous N days, same source",
              "z", "efficiency_pct", "Per record", "Not computed with fewer than the configured points or zero MAD", "STATISTICAL",
              "An unusual reading, not a diagnosis."),
    MetricDef("meters_gap_vs_cohort", "Meters gap vs peers", "Estimated meters a loom would have woven at its peer group's median efficiency",
              "meters x (cohort median eff / loom eff - 1)", "m", "meters, efficiency_pct", "Per loom over the period",
              "Only for cohorts of 3+ looms with the same category, width and style", "MODELED",
              "Assumes output scales with efficiency at unchanged RPM and style. A potential, not a realised loss."),
    MetricDef("air_nm3_per_meter", "Air per meter", "Compressed air per meter woven", "sum(air_nm3) / sum(meters)", "Nm3/m", "Air consumption (Nm3)",
              "Ratio of sums", "No value without measured air: the Tsudakoma exports report 0 for all looms (not measured)", "MEASURED"),
    MetricDef("kwh_per_meter", "Energy per meter", "Electricity per meter woven", "sum(kWh) / sum(meters)", "kWh/m", "energy_readings.kwh",
              "Ratio of sums over matching periods", "No value without a meter reading; never derived from RPM or efficiency", "MEASURED"),
]
BY_KEY: Dict[str, MetricDef] = {m.key: m for m in DEFINITIONS}


def weight(r: dict) -> float:
    if r.get("run_min") is not None and r.get("stop_min") is not None and (r["run_min"] + r["stop_min"]) > 0:
        return r["run_min"] + r["stop_min"]
    return SHIFT_MINUTES


def eff_weighted(rows: Iterable[dict]) -> Optional[float]:
    num = den = 0.0
    for r in rows:
        if r.get("efficiency_pct") is None:
            continue
        w = weight(r)
        num += r["efficiency_pct"] * w
        den += w
    return num / den if den else None


def _sum(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return (sum(vals) if vals else None), len(vals)


def rate_cmpx(rows: Iterable[dict], key: str) -> Optional[float]:
    stops = picks = 0.0
    n = 0
    for r in rows:
        if r.get(key) is None or not r.get("kilopicks"):
            continue
        stops += r[key]
        picks += r["kilopicks"]
        n += 1
    return stops / picks * 100 if n and picks else None


def aggregate(rows: List[dict]) -> dict:
    """All KPIs for a set of loom-shift rows, with coverage counts so gaps are visible."""
    meters, n_m = _sum(rows, "meters")
    kp, n_kp = _sum(rows, "kilopicks")
    warp, n_w = _sum(rows, "warp_stops")
    weft, n_f = _sum(rows, "weft_stops")
    n_eff = sum(1 for r in rows if r.get("efficiency_pct") is not None)
    return {
        "loom_shifts": len(rows),
        "looms": len({r["loom_id"] for r in rows}),
        "meters": meters, "kilopicks": kp,
        "efficiency_pct": eff_weighted(rows),
        "warp_stops": warp, "weft_stops": weft,
        "warp_stops_cmpx": rate_cmpx(rows, "warp_stops"),
        "weft_stops_cmpx": rate_cmpx(rows, "weft_stops"),
        "meters_per_loom_shift": meters / n_m if n_m else None,
        "coverage": {"meters": n_m, "kilopicks": n_kp, "efficiency_pct": n_eff, "warp_stops": n_w, "weft_stops": n_f},
    }


def median(vals: List[float]) -> Optional[float]:
    s = sorted(vals)
    n = len(s)
    if not n:
        return None
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def robust_z(x: float, history: List[float]) -> Optional[float]:
    m = median(history)
    if m is None:
        return None
    mad = median([abs(v - m) for v in history])
    if not mad:
        return None
    return (x - m) / (1.4826 * mad)

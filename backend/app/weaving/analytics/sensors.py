"""
Machine abnormality watch: early-warning signals from loom sensors, and a transparent composite health score.

Method (deterministic statistics, no black box):
  * Each sensor is reduced to a daily value per loom (mean over hours the loom was mostly running, so idle hours
    do not skew it).
  * The loom's own NORMAL level is found from its own history: the best single step in the daily series splits
    "before" from "after", and the "before" days give a median and a spread. A loom is compared with itself,
    not with a fixed number, because looms of different age and type run at different levels.
  * Recent level = the last 3 days. z = (recent - normal) / spread, in the direction that is worse. A minimum
    relative change is also required so a tiny but very consistent difference does not raise an alarm.
  * The trend over the last 7 days (least squares) gives a rough time to reach the alarm level, if one is set.
These are EARLY-WARNING SIGNALS. They have not been validated against real breakdowns (the demo data is synthetic)
and must not be presented as predictions of failure until they have been.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from app.weaving.analytics import stats
from app.weaving.analytics.context import AnalysisContext

RECENT_DAYS = 3
TREND_DAYS = 7
MIN_HISTORY_DAYS = 8


@dataclass(frozen=True)
class SensorSpec:
    key: str
    attr: str  # attribute of facts.SensorDay
    label: str
    unit: str
    worse: str  # "high" | "low" | "both"
    alarm: Optional[float]  # absolute alarm level (configurable per site); None when there is no standard level
    abs_floor: float  # smallest spread worth believing
    min_rel_change: float  # smallest relative change worth flagging
    meaning: str  # what a rise/fall usually points at, as a hypothesis to check


SPECS: Dict[str, SensorSpec] = {
    "vibration": SensorSpec("vibration", "vibration", "Vibration", "mm/s", "high", 4.5, 0.08, 0.08, "Wear or looseness in bearings, drive or sley mechanism, or a loose mounting."),
    "temperature": SensorSpec("temperature", "temperature", "Motor temperature", "°C", "high", 75.0, 0.6, 0.06, "Bearing friction, poor lubrication, blocked cooling, or an overloaded drive."),
    "pressure": SensorSpec("pressure", "pressure", "Main-nozzle air pressure", "bar", "low", 5.5, 0.03, 0.03, "A leak, a blocked filter, a regulator drift, or low supply pressure."),
    "power": SensorSpec("power", "power_kw", "Power draw", "kW", "both", None, 0.10, 0.08, "Load change, a drive or supply fault, or an unusual running pattern."),
}


@dataclass
class SensorAlert:
    loom_id: int
    loom: str
    kind: str  # DRIFT | SHIFT_POWER | SENSOR_OFFLINE
    sensor: str
    level: str  # CRITICAL | WARNING | WATCH
    title: str
    facts: List[str]
    recent: Optional[float] = None
    normal: Optional[float] = None
    unit: str = ""
    z: Optional[float] = None
    slope_per_day: Optional[float] = None
    days_to_alarm: Optional[float] = None
    started_on: Optional[str] = None
    hypothesis: Optional[str] = None
    n_days: int = 0
    limitations: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        d = dict(self.__dict__)
        for k in ("recent", "normal", "z", "slope_per_day", "days_to_alarm"):
            if d[k] is not None:
                d[k] = round(d[k], 2)
        return d


# ---------------------------------------------------------------------------- daily series

def daily_series(ctx: AnalysisContext, loom_id: int, sensor: str, shift_id: Optional[int] = None) -> List[Tuple[date, float]]:
    attr = SPECS[sensor].attr
    num: Dict[date, float] = defaultdict(float)
    den: Dict[date, float] = defaultdict(float)
    for r in ctx.sensor_days:
        if r.loom_id != loom_id or (shift_id is not None and r.shift_id != shift_id):
            continue
        v = getattr(r, attr)
        if v is None:
            continue
        w = max(r.with_sensors, 1)
        num[r.shift_date] += v * w
        den[r.shift_date] += w
    return sorted((d, num[d] / den[d]) for d in num)


def _slope(points: List[Tuple[date, float]]) -> Tuple[Optional[float], Optional[float]]:
    """Least-squares slope per day and its t statistic."""
    n = len(points)
    if n < 4:
        return None, None
    xs = [(d - points[0][0]).days for d, _ in points]
    ys = [v for _, v in points]
    mx, my = stats.mean(xs), stats.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return None, None
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    resid = [y - (my + slope * (x - mx)) for x, y in zip(xs, ys)]
    se = math.sqrt(sum(r * r for r in resid) / max(n - 2, 1) / sxx) or 1e-9
    return slope, slope / se


def _normal_level(values: List[float], spec: SensorSpec) -> Optional[dict]:
    """The loom's own normal level: the 'before' side of its best step change, else everything but the most recent days."""
    if len(values) < MIN_HISTORY_DAYS:
        return None
    shift = stats.level_shift(values, min_segment=3)
    if shift and (shift["after_mean"] - shift["before_mean"]) * (1 if spec.worse != "low" else -1) > 0 and shift["n_after"] >= 2:
        base = values[: shift["index"]]
        started = shift["index"]
    else:
        base = values[:-RECENT_DAYS]
        started = None
    if len(base) < 5:
        return None
    center = stats.median(base)
    mad = stats.median([abs(v - center) for v in base]) * 1.4826
    spread = max(mad, stats.stdev(base) * 0.7, spec.abs_floor, abs(center) * 0.01)
    return {"center": center, "spread": spread, "n_base": len(base), "started_index": started}


# ---------------------------------------------------------------------------- detection

def detect_alerts(ctx: AnalysisContext) -> List[SensorAlert]:
    refs = ctx.refs
    alerts: List[SensorAlert] = []
    by_loom: Dict[int, List] = defaultdict(list)
    for r in ctx.sensor_days:
        by_loom[r.loom_id].append(r)
    for loom_id in sorted(by_loom, key=lambda i: refs.loom_code(i)):
        code = refs.loom_code(loom_id)
        for key, spec in SPECS.items():
            series = daily_series(ctx, loom_id, key)
            if not series:
                continue
            values = [v for _, v in series]
            level = _normal_level(values, spec)
            if not level:
                continue
            recent_vals = values[-RECENT_DAYS:]
            recent = stats.mean(recent_vals)
            sign = {"high": 1, "low": -1, "both": 1 if recent >= level["center"] else -1}[spec.worse]
            z = sign * (recent - level["center"]) / level["spread"]
            rel = abs(recent - level["center"]) / max(abs(level["center"]), 1e-9)
            slope, t = _slope(series[-TREND_DAYS:])
            drifting = slope is not None and t is not None and sign * slope > 0 and abs(t) >= 3
            beyond_alarm = spec.alarm is not None and ((spec.worse == "high" and recent >= spec.alarm) or (spec.worse == "low" and recent <= spec.alarm))
            if rel < spec.min_rel_change and not beyond_alarm:
                continue
            if beyond_alarm or z >= 10:
                lvl = "CRITICAL"
            elif z >= 5:
                lvl = "WARNING"
            elif z >= 3 and drifting:
                lvl = "WATCH"
            else:
                continue
            days_to_alarm = None
            if spec.alarm is not None and slope and sign * slope > 0 and not beyond_alarm:
                gap = (spec.alarm - recent) if spec.worse == "high" else (recent - spec.alarm)
                if gap > 0:
                    d = gap / abs(slope)
                    days_to_alarm = d if d <= 30 else None
            started = None
            if level["started_index"] is not None:
                started = series[level["started_index"]][0].isoformat()
            direction = "above" if recent > level["center"] else "below"
            facts = [
                f"{spec.label} on {code} averaged {recent:.2f} {spec.unit} over the last {RECENT_DAYS} days, {direction} its own normal of {level['center']:.2f} {spec.unit} "
                f"(spread {level['spread']:.2f}; z = {z:+.1f}; {rel * 100:.0f}% change).",
            ]
            if started:
                facts.append(f"The change began around {started}.")
            if slope is not None and abs(t or 0) >= 2:
                facts.append(f"Over the last {min(len(series), TREND_DAYS)} days it is moving {slope:+.2f} {spec.unit} per day (t = {t:.1f}).")
            if days_to_alarm is not None:
                facts.append(f"At that rate it would reach the {spec.alarm:g} {spec.unit} alarm level in about {days_to_alarm:.0f} day(s). A straight-line extrapolation, not a prediction.")
            if beyond_alarm:
                facts.append(f"It is already past the {spec.alarm:g} {spec.unit} alarm level.")
            alerts.append(SensorAlert(
                loom_id=loom_id, loom=code, kind="DRIFT", sensor=key, level=lvl, title=f"{spec.label} {'high' if direction == 'above' else 'low'} on {code}", facts=facts, recent=recent, normal=level["center"],
                unit=spec.unit, z=z, slope_per_day=slope, days_to_alarm=days_to_alarm, started_on=started, hypothesis=spec.meaning, n_days=len(series),
                limitations=["Early-warning signal, not validated against real failures.", "Alarm levels are typical values and should be set per machine make."]))
        alerts += _offline(ctx, loom_id, code, by_loom[loom_id])
        alerts += _shift_power(ctx, loom_id, code)
    order = {"CRITICAL": 0, "WARNING": 1, "WATCH": 2}
    return sorted(alerts, key=lambda a: (order[a.level], -(a.z or 0)))


def _offline(ctx: AnalysisContext, loom_id: int, code: str, rows: List) -> List[SensorAlert]:
    end = ctx.window.end_date
    recent_start = end - timedelta(days=1)
    base_end = end - timedelta(days=8)  # keep the comparison period clear of the days being judged
    rec = [r for r in rows if r.shift_date >= recent_start]
    base = [r for r in rows if r.shift_date <= base_end]
    if not rec or sum(r.readings for r in base) < 100:
        return []
    miss = lambda rs: 1 - sum(r.with_sensors for r in rs) / max(sum(r.readings for r in rs), 1)
    m_rec, m_base = miss(rec), miss(base)
    if m_rec >= 0.2 and m_rec >= 3 * max(m_base, 0.03):
        return [SensorAlert(loom_id=loom_id, loom=code, kind="SENSOR_OFFLINE", sensor="all", level="WARNING", title=f"Sensors on {code} are dropping out",
                            facts=[f"{m_rec * 100:.0f}% of hourly readings on {code} had no sensor values in the last 2 days, against {m_base * 100:.0f}% earlier.",
                                   "While sensors are offline the abnormality watch cannot see this loom."], hypothesis="A loose connector, gateway fault or sensor failure.", n_days=len(rows),
                            limitations=["Output (picks) is still counted; only the machine-health signals are missing."])]
    return []


def _shift_power(ctx: AnalysisContext, loom_id: int, code: str) -> List[SensorAlert]:
    """Power draw in one shift well above the loom's other shifts, tested on daily values."""
    refs = ctx.refs
    end = ctx.window.end_date
    start = end - timedelta(days=13)
    per: Dict[int, Dict[date, float]] = defaultdict(dict)
    for sid in refs.shifts:
        for d, v in daily_series(ctx, loom_id, "power", sid):
            if start <= d <= end:
                per[sid][d] = v
    out = []
    for sid, series in per.items():
        others = [v for o, s in per.items() if o != sid for v in s.values()]
        mine = list(series.values())
        if len(mine) < 5 or len(others) < 10:
            continue
        ratio = stats.mean(mine) / stats.mean(others)
        se = math.sqrt(stats.stdev(mine) ** 2 / len(mine) + stats.stdev(others) ** 2 / len(others)) or 1e-9
        t = (stats.mean(mine) - stats.mean(others)) / se
        if ratio >= 1.12 and t >= 4:
            out.append(SensorAlert(loom_id=loom_id, loom=code, kind="SHIFT_POWER", sensor="power", level="WARNING", title=f"{code} draws more power in {refs.shift_name(sid)}",
                                   facts=[f"{code} averaged {stats.mean(mine):.2f} kW in {refs.shift_name(sid)} against {stats.mean(others):.2f} kW in its other shifts over {len(mine)} days (+{(ratio - 1) * 100:.0f}%, t = {t:.1f})."],
                                   recent=stats.mean(mine), normal=stats.mean(others), unit="kW", z=t, hypothesis="Supply voltage dips or load differences at that time of day, or a drive fault that shows only then.", n_days=len(mine),
                                   limitations=["Compares the loom's shifts with each other; it does not know which level is 'right'."]))
    return out


# ---------------------------------------------------------------------------- health score

HEALTH_NOTE = "A composite indicator for ordering attention, 100 = no concern. It is not a probability of failure."


def machine_health(ctx: AnalysisContext, alerts: List[SensorAlert], declines: set, pm_overdue_days: Dict[int, int], mech_ratio: Dict[int, float]) -> Dict[int, dict]:
    """
    Per loom: start at 100 and subtract, each shown separately:
      sensor alerts   critical 30 / warning 15 / watch 7 each (capped at 45)
      stoppage record mechanical+electrical stop rate vs same-type looms: >=3x -20, >=2x -10
      overdue PM      5 per week overdue (capped at 15)
      performance     -10 if the loom is below its own earlier efficiency (loom_decline finding)
      service age     -5 if more than 600 days since the last overhaul
    """
    refs = ctx.refs
    out: Dict[int, dict] = {}
    pts = {"CRITICAL": 30, "WARNING": 15, "WATCH": 7}
    for loom_id, loom in refs.looms.items():
        comp = []
        sens = sum(pts[a.level] for a in alerts if a.loom_id == loom_id and a.kind != "SENSOR_OFFLINE")
        if sens:
            comp.append(("Sensor alerts", -min(45, sens), ", ".join(sorted({f"{SPECS[a.sensor].label if a.sensor in SPECS else a.sensor} ({a.level.lower()})" for a in alerts if a.loom_id == loom_id and a.kind != 'SENSOR_OFFLINE'}))))
        r = mech_ratio.get(loom_id, 0.0)
        if r >= 3:
            comp.append(("Stoppage record", -20, f"mechanical/electrical stops {r:.1f}x similar looms"))
        elif r >= 2:
            comp.append(("Stoppage record", -10, f"mechanical/electrical stops {r:.1f}x similar looms"))
        od = pm_overdue_days.get(loom_id, 0)
        if od > 0:
            comp.append(("Overdue maintenance", -min(15, math.ceil(od / 7) * 5), f"preventive maintenance {od} days overdue"))
        if loom_id in declines:
            comp.append(("Performance", -10, "efficiency below its own earlier level"))
        if loom.last_overhaul_on and (ctx.today - loom.last_overhaul_on).days > 600:
            comp.append(("Service age", -5, f"{(ctx.today - loom.last_overhaul_on).days} days since overhaul"))
        score = max(0, 100 + sum(c[1] for c in comp))
        out[loom_id] = {"score": score, "band": "HEALTHY" if score >= 80 else "WATCH" if score >= 60 else "AT_RISK",
                        "components": [{"factor": f, "points": p, "detail": d} for f, p, d in comp], "note": HEALTH_NOTE}
    return out

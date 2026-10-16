"""
Short-horizon forecasting of daily output, with its own track record.

Two simple methods are tried (simple exponential smoothing, and a damped-trend version), and the one with the lower
error on a hold-out of the most recent days is used. The error (MAPE, mean absolute percentage error) is reported
next to every forecast: a forecast that has not been checked against what actually happened should not be trusted,
and this one shows how it did.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from app.weaving.analytics import stats


def _ses(series: Sequence[float], alpha: float) -> float:
    level = series[0]
    for y in series[1:]:
        level = alpha * y + (1 - alpha) * level
    return level


def _damped(series: Sequence[float], alpha: float = 0.5, beta: float = 0.2, phi: float = 0.85) -> Tuple[float, float]:
    level, trend = series[0], (series[1] - series[0]) if len(series) > 1 else 0.0
    for y in series[1:]:
        prev = level
        level = alpha * y + (1 - alpha) * (prev + phi * trend)
        trend = beta * (level - prev) + (1 - beta) * phi * trend
    return level, trend


def _predict(method: str, series: Sequence[float], horizon: int) -> List[float]:
    if method == "ses":
        return [_ses(series, 0.4)] * horizon
    level, trend = _damped(series)
    out, acc = [], 0.0
    for h in range(1, horizon + 1):
        acc += 0.85 ** h
        out.append(level + trend * acc)
    return out


@dataclass
class Forecast:
    method: str
    points: List[float]
    low: List[float]
    high: List[float]
    mape_pct: Optional[float]
    backtest_days: int
    note: str

    def as_dict(self) -> dict:
        return {"method": self.method, "points": [round(x, 1) for x in self.points], "low": [round(x, 1) for x in self.low], "high": [round(x, 1) for x in self.high],
                "mape_pct": None if self.mape_pct is None else round(self.mape_pct, 1), "backtest_days": self.backtest_days, "note": self.note}


def forecast_daily(series: Sequence[float], horizon: int = 7, holdout: int = 5) -> Optional[Forecast]:
    """Needs at least ~10 days. Returns None when there is too little history to forecast honestly."""
    series = [float(x) for x in series]
    if len(series) < holdout + 5:
        return None
    errors = {"ses": [], "damped": []}
    for k in range(holdout, 0, -1):  # rolling origin: forecast each of the last `holdout` days from the days before it
        train, actual = series[:-k], series[-k]
        for method in errors:
            pred = _predict(method, train, 1)[0]
            if actual > 0:
                errors[method].append(abs(pred - actual) / actual * 100.0)
    best = min(errors, key=lambda m: stats.mean(errors[m]) if errors[m] else math.inf)
    mape = stats.mean(errors[best]) if errors[best] else None
    pts = _predict(best, series, horizon)
    resid = [series[i] - _predict(best, series[:i], 1)[0] for i in range(max(4, len(series) - 10), len(series))]
    sd = stats.stdev(resid) if len(resid) > 2 else 0.0
    z = 1.2816  # 80% interval
    low = [max(0.0, p - z * sd * math.sqrt(1 + 0.3 * i)) for i, p in enumerate(pts)]
    high = [p + z * sd * math.sqrt(1 + 0.3 * i) for i, p in enumerate(pts)]
    return Forecast(best, pts, low, high, mape, holdout, f"{'Exponential smoothing' if best == 'ses' else 'Damped-trend smoothing'}; MAPE over the last {holdout} days shown. 80% band.")

"""
Small, dependency-free statistics used to decide whether a difference is a signal or noise.
These produce *signals*, not causes: a low p-value says a difference is unlikely to be chance,
not why it happened.
"""
from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple


def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs)


def stdev(xs: Sequence[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def median(xs: Sequence[float]) -> float:
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def _log_binom_pmf(k: int, n: int, p: float) -> float:
    if p <= 0.0:
        return 0.0 if k == 0 else -math.inf
    if p >= 1.0:
        return 0.0 if k == n else -math.inf
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1) + k * math.log(p) + (n - k) * math.log1p(-p)


def binomial_sf(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p), exact."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    # Sum the shorter tail for accuracy.
    total = sum(math.exp(_log_binom_pmf(i, n, p)) for i in range(k, n + 1))
    return min(1.0, total)


def rate_ratio_test(events_a: int, exposure_a: float, events_b: int, exposure_b: float) -> Tuple[Optional[float], Optional[float]]:
    """
    Is the event rate in group A higher than in group B? Returns (rate ratio A/B, one-sided p-value).

    Conditional exact test for two Poisson rates: given the total number of events, the count in A
    is Binomial(total, exposure_a / (exposure_a + exposure_b)) if the rates are equal.
    """
    if exposure_a <= 0 or exposure_b <= 0:
        return None, None
    total = events_a + events_b
    rate_a, rate_b = events_a / exposure_a, events_b / exposure_b
    ratio = rate_a / rate_b if rate_b > 0 else (math.inf if rate_a > 0 else None)
    if total == 0:
        return ratio, 1.0
    return ratio, binomial_sf(events_a, total, exposure_a / (exposure_a + exposure_b))


def poisson_sf(k: int, lam: float) -> float:
    """P(X >= k) for X ~ Poisson(lam), exact."""
    if k <= 0:
        return 1.0
    if lam <= 0:
        return 0.0
    cdf = sum(math.exp(-lam + i * math.log(lam) - math.lgamma(i + 1)) for i in range(k))
    return max(0.0, 1.0 - cdf)


def share_concentration_test(count_in_group: int, total: int, expected_share: float) -> Optional[float]:
    """One-sided exact p-value that `count_in_group` of `total` events fall in a group expected to receive `expected_share`."""
    if total <= 0 or not 0 < expected_share < 1:
        return None
    return binomial_sf(count_in_group, total, expected_share)


def normal_sf(z: float) -> float:
    return 0.5 * math.erfc(z / math.sqrt(2))


def level_shift(series: Sequence[float], min_segment: int = 3) -> Optional[dict]:
    """
    Best single step change in a series: the split that minimises the within-segment squared error.
    Returns index of the first point after the change, both segment means, and an approximate
    one-sided p-value for "the later segment is lower" (Welch t treated as normal, so it is only
    roughly calibrated; effect size is the more reliable guide).
    """
    n = len(series)
    if n < 2 * min_segment:
        return None
    best = None
    for i in range(min_segment, n - min_segment + 1):
        a, b = series[:i], series[i:]
        sse = sum((x - mean(a)) ** 2 for x in a) + sum((x - mean(b)) ** 2 for x in b)
        if best is None or sse < best[0]:
            best = (sse, i)
    assert best is not None
    i = best[1]
    a, b = series[:i], series[i:]
    se = math.sqrt(max(stdev(a), 0.5) ** 2 / len(a) + max(stdev(b), 0.5) ** 2 / len(b))  # sd floored: avoids infinite t on flat series
    t = (mean(a) - mean(b)) / se
    return {"index": i, "before_mean": mean(a), "after_mean": mean(b), "n_before": len(a), "n_after": len(b), "t": t, "p_lower": normal_sf(t)}

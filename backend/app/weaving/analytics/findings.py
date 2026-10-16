"""Shared building blocks for findings: confidence rules, the priority score, and common limitation notes."""
from __future__ import annotations

from typing import List, Optional

from app.schemas.weaving_intel import Confidence, Finding
from app.weaving.analytics.calc import ProdAgg

# Confidence is a rule, not a feeling. Thresholds are deliberately conservative, because many looms,
# beams and shifts are compared at once and some "significant" results are expected by chance alone.
HIGH_P, HIGH_N, HIGH_DAYS = 0.001, 30, 7
MED_P, MED_N, MED_DAYS = 0.01, 10, 3

CONF_WEIGHT = {"HIGH": 1.0, "MEDIUM": 0.6, "LOW": 0.3}
SEVERITY_BASE = {"HIGH": 0.5, "MEDIUM": 0.2, "LOW": 0.05}  # lets findings with no rupee estimate still rank


def confidence(p_value: Optional[float], n_events: int, n_days: int, missing: Optional[List[str]] = None, extra: Optional[List[str]] = None) -> Confidence:
    missing = list(missing or [])
    reasons = list(extra or [])
    if p_value is not None and p_value <= HIGH_P and n_events >= HIGH_N and n_days >= HIGH_DAYS:
        level = "HIGH"
    elif p_value is not None and p_value <= MED_P and n_events >= MED_N and n_days >= MED_DAYS:
        level = "MEDIUM"
    else:
        level = "LOW"
    reasons.append(f"{n_events} observations over {n_days} production day(s)")
    if p_value is not None:
        reasons.append(f"p ≈ {p_value:.2g} (HIGH needs p ≤ {HIGH_P} with ≥{HIGH_N} observations over ≥{HIGH_DAYS} days; MEDIUM needs p ≤ {MED_P}, ≥{MED_N}, ≥{MED_DAYS} days)")
    else:
        reasons.append("no significance test available")
    return Confidence(level=level, reasons=reasons, missing_information=missing)


def priority_score(severity: str, conf_level: str, impact_lakhs: Optional[float]) -> float:
    """
    Ordering heuristic for "what to look at first": (estimated impact in lakh + a small severity base)
    weighted by confidence. It ranks work; it is not a forecast of savings.
    """
    w = CONF_WEIGHT[conf_level]
    return round(((impact_lakhs or 0.0) + SEVERITY_BASE[severity]) * w, 4)


def data_limitations(agg: ProdAgg) -> List[str]:
    out: List[str] = []
    if agg.no_picks:
        out.append(f"{agg.no_picks} of {agg.readings} readings had no pick count and were excluded from efficiency (not treated as zero).")
    if agg.partial:
        out.append(f"{agg.partial} readings were flagged PARTIAL (counter reset) and are included as recorded.")
    if agg.demo:
        out.append("Includes DEMONSTRATION data; these are not the mill's own records.")
    return out


def lakhs(x: Optional[float]) -> str:
    return "n/a" if x is None else f"₹{x:.2f} L"


def sort_findings(findings: List[Finding]) -> List[Finding]:
    return sorted(findings, key=lambda f: (-f.priority_score, f.key))

"""
Metric definitions. This is the single place that says what every number means; the API publishes it
at GET /weaving/analytics/definitions and the code in calc.py implements exactly these formulas.
"""
from dataclasses import dataclass
from typing import List

PICKS_PER_METRE_PER_PPI = 39.3701  # inches in a metre: picks per metre of fabric = PPI x 39.3701


@dataclass(frozen=True)
class MetricDef:
    key: str
    name: str
    unit: str
    formula: str
    exclusions: str
    missing_data: str


DEFINITIONS: List[MetricDef] = [
    MetricDef(
        "scheduled_time", "Scheduled time", "hours",
        "Sum of the length of every loom reading in the window (readings are normally one hour).",
        "Looms with no readings contribute nothing: a loom with no data is not assumed to have been idle or running.",
        "Gaps in a loom's readings reduce scheduled time instead of counting as downtime. Reading coverage is reported.",
    ),
    MetricDef(
        "utilization", "Utilization (availability)", "%",
        "running time / scheduled time x 100.",
        "Planned stops (beam change, style change, planned maintenance) are NOT removed; they are part of scheduled time. "
        "Use the stoppage breakdown to separate them.",
        "Readings are all counted; there is no missing running time because a counter fault still records run time.",
    ),
    MetricDef(
        "loom_efficiency", "Loom efficiency", "%",
        "picks inserted / (rated loom speed in picks per minute x scheduled minutes) x 100, summed over looms for a group.",
        "Readings with no pick counter value (NO_PICKS) are excluded from BOTH the numerator and the denominator, "
        "so a faulty counter does not look like poor efficiency.",
        "Reported with the number of readings excluded. Not called OEE: availability, performance and quality are not "
        "separately defined here.",
    ),
    MetricDef(
        "fabric_meters", "Fabric produced", "metres",
        "picks inserted / (style PPI x 39.3701).",
        "Readings with no pick counter or no style.",
        "Loom-state metres: take-up, shrinkage and rejected fabric are not deducted.",
    ),
    MetricDef(
        "target_meters", "Target fabric", "metres",
        "style target efficiency % x rated speed x scheduled minutes / (style PPI x 39.3701), over the same readings as fabric produced.",
        "Same readings as fabric produced.",
        "Looms with no style assigned have no target.",
    ),
    MetricDef(
        "achievement", "Achievement against target", "%",
        "fabric produced / target fabric x 100.", "As fabric produced.", "None when there is no target.",
    ),
    MetricDef(
        "stops_per_100k", "Stops per 100,000 picks", "stops / 10^5 picks",
        "unplanned stop events that STARTED in the window / picks inserted in the window x 100,000.",
        "Planned stops (reasons flagged as not counting toward stop rate) are excluded. Warp-stop and weft-stop rates use "
        "the same denominator, so they add up to the all-cause rate.",
        "Picks come from readings with a counter value; a group with no picks has no rate.",
    ),
    MetricDef(
        "stop_duration", "Average stoppage duration", "minutes",
        "mean of (end - start) over UNPLANNED stop events that started in the window AND have ended.",
        "Planned stops (beam change, style change, planned maintenance) are excluded because they are scheduled, long and would distort the average. Stops still open are excluded (their length so far is unknown) and counted separately as open stoppages.",
        "Open stops are included in downtime-to-date, using the time up to now.",
    ),
    MetricDef(
        "downtime", "Downtime", "minutes",
        "sum over stop events of the part of each stop that falls inside the window (clipped at both ends).",
        "None; planned and unplanned are reported separately. A stop is attributed to the shift, style, beam and weaver "
        "in effect when it STARTED, even if it runs into the next shift.",
        "An open stop counts up to the current time.",
    ),
    MetricDef(
        "defect_rate", "Defects per 100 m", "defects / 100 m",
        "defect observations (count) / metres inspected x 100.",
        "Only inspected fabric is in the denominator. Fabric not yet inspected is not assumed clean.",
        "Inspection coverage (metres inspected / metres produced) is reported; low coverage lowers confidence.",
    ),
    MetricDef(
        "defect_points", "Defect points per 100 m", "points / 100 m",
        "sum of (4-point-system points x count) / metres inspected x 100.",
        "As defects per 100 m.", "As defects per 100 m.",
    ),
    MetricDef(
        "grade_a", "First-grade (A) share", "%",
        "metres of rolls graded A / metres inspected x 100.", "Uninspected fabric.", "None when nothing was inspected.",
    ),
    MetricDef(
        "downtime_impact", "Estimated impact of downtime", "metres, rupees (lakh)",
        "downtime minutes x the loom's observed running output (metres per running minute in the window) = metres not woven; "
        "x the style's contribution per metre (rate - variable cost) = rupees.",
        "Estimate only. Assumes the loom would have run at its recent average speed and every metre would have sold.",
        "Falls back to rated speed x style target efficiency when a loom has no readings; none when the style is unknown.",
    ),
]

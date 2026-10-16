"""
Response models for evidence-backed findings.

Every finding keeps four things apart, because they are not the same kind of claim:
  facts          what the data directly shows ("AJ-14 ran 78.2% over the last 6 days; its baseline was 89.9%")
  signals        statistical tests that say a difference is unlikely to be chance
  hypotheses     plausible explanations, always UNVERIFIED, each with how to check it
  verified_cause only ever filled from a completed action's recorded outcome (never inferred), None otherwise
"""
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field

Scalar = Union[str, int, float, bool, None]


class ImpactEstimate(BaseModel):
    lost_m: float
    lost_lakhs: Optional[float] = None
    assumptions: List[str] = Field(default_factory=list)


class Evidence(BaseModel):
    period: str
    scope: Dict[str, str]
    observed: Dict[str, Scalar]
    baseline: Dict[str, Scalar] = Field(default_factory=dict)
    n_observations: int
    estimated_impact: Optional[ImpactEstimate] = None
    limitations: List[str] = Field(default_factory=list)


class Signal(BaseModel):
    name: str
    method: str
    statistic: Optional[float] = None
    p_value: Optional[float] = None
    note: Optional[str] = None


class Hypothesis(BaseModel):
    statement: str
    status: str = "UNVERIFIED"
    how_to_check: str


class Confidence(BaseModel):
    level: str  # HIGH | MEDIUM | LOW
    reasons: List[str]
    missing_information: List[str] = Field(default_factory=list)


class Finding(BaseModel):
    key: str  # stable id, e.g. "loom_decline:AJ-14"; WvAction.finding_key points at it
    kind: str  # loom_decline | recurring_stop | beam_warp_excess | shift_defect_shift | maintenance_priority
    severity: str  # HIGH | MEDIUM | LOW
    title: str
    facts: List[str]
    evidence: Evidence
    signals: List[Signal] = Field(default_factory=list)
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    confidence: Confidence
    priority_score: float
    requires_human_approval: bool = True
    verified_cause: Optional[str] = None
    audiences: List[str] = Field(default_factory=list)  # roles this finding is for
    link: str = "/weaving"


class Page(BaseModel):
    page: int
    page_size: int
    total: int


class StopEventOut(BaseModel):
    id: int
    loom: str
    started_at: str
    ended_at: Optional[str]
    duration_min: Optional[float]
    open: bool
    reason: str
    category: str
    planned: bool
    shift: str
    style: Optional[str]
    beam: Optional[str]


class StopEventPage(Page):
    items: List[StopEventOut]


class InspectionOut(BaseModel):
    id: int
    roll_no: str
    loom: str
    style: str
    beam: Optional[str]
    shift: str
    shift_date: str
    inspected_at: str
    length_m: float
    grade: str
    defects: int
    points: int


class InspectionPage(Page):
    items: List[InspectionOut]

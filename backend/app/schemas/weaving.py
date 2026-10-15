from typing import List, Dict, Optional
from pydantic import BaseModel


class WeavingKpis(BaseModel):
    fabric_m: float
    target_m: float
    achievement_pct: float
    efficiency_pct: float
    grade_a_pct: float
    loss_lakhs: float
    loss_m: float
    revenue_lakhs: float
    # change versus the previous window of the same length (percentage points for pct fields)
    fabric_change_pct: float
    efficiency_change_pts: float
    grade_a_change_pts: float
    loss_change_pct: float
    looms_total: int
    looms_running: int
    looms_stopped: int
    looms_idle: int


class WeavingDecision(BaseModel):
    id: str
    severity: str  # HIGH | MEDIUM | LOW
    title: str
    why: str
    action: str
    owner: str
    impact_lakhs: float
    link: str  # frontend route to see the evidence


class WeavingTrendPoint(BaseModel):
    date_label: str
    actual_m: float
    target_m: float
    efficiency_pct: float
    grade_a_pct: float
    loss_lakhs: float


class WeavingShiftRow(BaseModel):
    shift: str
    actual_m: float
    target_m: float
    efficiency_pct: float
    grade_a_pct: float
    top_stop_reason: str


class WeavingGroupRow(BaseModel):
    loom_type: str
    looms: int
    actual_m: float
    target_m: float
    efficiency_pct: float
    grade_a_pct: float
    loss_lakhs: float


class WeavingLoom(BaseModel):
    loom_id: str
    loom_type: str
    style: str
    status: str  # RUNNING | STOPPED | IDLE
    health: str  # NORMAL | ATTENTION | CRITICAL
    rpm: int
    efficiency_pct: float
    actual_m: float
    target_m: float
    loss_m: float
    loss_lakhs: float
    grade_a_pct: float
    defects_per_100m: float
    stops: int
    stop_reason: Optional[str] = None
    stopped_since_min: int = 0
    weaver: str
    fitter: str
    main_issue: str
    trend: List[float]  # daily efficiency, oldest first (last 14 days)


class WeavingStopCause(BaseModel):
    cause: str
    minutes: int
    stops: int
    loss_lakhs: float
    share_pct: float
    advice: str


class WeavingDefect(BaseModel):
    defect: str
    count: int
    share_pct: float


class WeavingQuality(BaseModel):
    grade_a_pct: float
    grade_b_pct: float
    grade_c_pct: float
    defects_per_100m: float
    rejected_m: float
    downgrade_loss_lakhs: float
    defect_types: List[WeavingDefect]
    worst_looms: List[Dict[str, object]]


class WeavingStyle(BaseModel):
    style: str
    fabric: str
    meters: float
    rate_per_m: float
    cost_per_m: float
    margin_pct: float
    profit_lakhs: float
    grade_a_pct: float
    efficiency_pct: float
    recommendation: str  # PUSH | HOLD | REPRICE | STOP
    reason: str


class WeavingDeptStaff(BaseModel):
    department: str
    required: int
    available: int
    gap: int
    avg_grade: str
    status: str


class WeavingGradeCount(BaseModel):
    grade: str
    count: int


class WeavingShiftStaff(BaseModel):
    shift: str
    looms_per_weaver: float
    output_per_weaver_m: float
    absent: int
    status: str


class WeavingPeople(BaseModel):
    headcount: int
    available_today: int
    absenteeism_pct: float
    departments: List[WeavingDeptStaff]
    grades: List[WeavingGradeCount]
    shifts: List[WeavingShiftStaff]
    promotion_ready: int
    needs_training: int


class WeavingPmItem(BaseModel):
    loom_id: str
    task: str
    due_date: str
    days_overdue: int
    status: str  # OVERDUE | DUE_SOON | OK


class WeavingMaintenance(BaseModel):
    mtbf_hours: float
    mttr_min: float
    breakdowns: int
    pm_overdue: int
    pm_due_soon: int
    pm_compliance_pct: float
    items: List[WeavingPmItem]


class WeavingAction(BaseModel):
    id: str
    issue: str
    action: str
    owner: str
    due: str
    status: str  # OPEN | IN_PROGRESS | COMPLETED
    impact_lakhs: float


class WeavingModuleResponse(BaseModel):
    data_source: str = "MOCK"
    period: str
    period_label: str
    days: int
    verdict: str
    kpis: WeavingKpis
    decisions: List[WeavingDecision]
    trend: List[WeavingTrendPoint]
    shifts: List[WeavingShiftRow]
    groups: List[WeavingGroupRow]
    looms: List[WeavingLoom]
    stop_causes: List[WeavingStopCause]
    quality: WeavingQuality
    styles: List[WeavingStyle]
    people: WeavingPeople
    maintenance: WeavingMaintenance
    actions: List[WeavingAction]

from typing import List, Optional
from pydantic import BaseModel

class TopPriorityData(BaseModel):
    priority_level: str  # CRITICAL | HIGH | MEDIUM
    badge_label: str     # e.g., "🔴 HIGH PRIORITY"
    title: str           # e.g., "Production is below target"
    sub_highlight: str   # e.g., "Short by 2,380 kg"
    main_contributor: str # e.g., "Machine downtime"
    most_affected_machine_type: str # e.g., "Vortex"
    most_affected_machine_id: str   # e.g., "V-09"
    actual_kg: float
    target_kg: float
    gap_kg: float
    target_tab: str      # e.g., "production"

class WhyContributor(BaseModel):
    category: str        # e.g., "Machine Downtime", "Efficiency Loss", "Power Events"
    percentage: float    # e.g., 47.0
    status_color: str    # "RED" | "ORANGE" | "YELLOW"
    detail_text: Optional[str] = None

class SecondaryMachineContributor(BaseModel):
    machine_id: str      # e.g., "V-05"
    machine_type: str    # e.g., "Vortex"
    loss_kg: float       # e.g., -420.0
    status_color: str    # "RED" | "ORANGE" | "YELLOW"

class WhereLocationData(BaseModel):
    primary_machine_id: str       # e.g., "V-09"
    primary_machine_type: str     # e.g., "Vortex Spinning"
    primary_section: str          # e.g., "Spinning Unit 1"
    production_loss_kg: float     # e.g., -680.0
    efficiency_pct: float         # e.g., 84.2
    downtime_minutes: int         # e.g., 240
    status: str                   # "🔴 Critical"
    secondary_machines: List[SecondaryMachineContributor]

class RecommendedAction(BaseModel):
    id: str
    step_number: int
    action_text: str               # e.g., "Investigate repeated downtime on V-09"
    button_label: str              # e.g., "View Machine"
    target_tab: str                # e.g., "machines"
    target_id: Optional[str] = None # e.g., "V-09"

class IfContinuesData(BaseModel):
    current_daily_gap_kg: float    # e.g., -2380.0
    projected_7d_gap_kg: float     # e.g., -16660.0
    projected_30d_gap_kg: float    # e.g., -71400.0
    label: str                     # "Estimated production impact"
    disclaimer_note: str           # "Projection assumes the current daily gap continues."

class OtherIssueItem(BaseModel):
    id: str
    status_icon: str               # "🟠" | "🟡" | "🔴"
    category: str                  # e.g., "Manpower shortage"
    location_or_area: str          # e.g., "Spinning"
    impact_detail: str             # e.g., "-30 workers"
    target_tab: Optional[str] = None

class ActionTrackerItem(BaseModel):
    id: str
    issue: str                     # e.g., "V-09 downtime"
    action: str                    # e.g., "Check motor + power events"
    owner: str                     # e.g., "Maintenance Manager"
    status: str                    # "OPEN" | "IN_PROGRESS" | "COMPLETED"
    status_badge: str              # "🔴 OPEN" | "🟠 IN PROGRESS" | "🟢 COMPLETED"
    created_date: str              # e.g., "2026-09-23"

class AIInsightData(BaseModel):
    summary_paragraph: str
    recommended_focus: str
    evidence_confidence: str       # e.g., "HIGH"
    facts: List[str]
    projections: List[str]

class DecisionCenterData(BaseModel):
    company_name: str
    selected_unit: str
    selected_period: str
    user_role: str
    permitted_section: Optional[str] = None
    
    top_priority: TopPriorityData
    why_contributors: List[WhyContributor]
    where_location: WhereLocationData
    recommended_actions: List[RecommendedAction]
    if_continues: IfContinuesData
    other_issues: List[OtherIssueItem]
    action_tracker: List[ActionTrackerItem]
    ai_insight: AIInsightData

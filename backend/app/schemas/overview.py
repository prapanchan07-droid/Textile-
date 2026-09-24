from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class TimePeriod(str, Enum):
    TODAY = "TODAY"
    SHIFT = "SHIFT"
    YESTERDAY = "YESTERDAY"
    THIS_WEEK = "THIS_WEEK"
    THIS_MONTH = "THIS_MONTH"

class ComparisonPeriod(str, Enum):
    PREVIOUS_SHIFT = "PREVIOUS_SHIFT"
    PREVIOUS_DAY = "PREVIOUS_DAY"
    PREVIOUS_WEEK = "PREVIOUS_WEEK"
    PREVIOUS_MONTH = "PREVIOUS_MONTH"
    THREE_MONTH_AVG = "THREE_MONTH_AVG"

class PerformanceStatus(str, Enum):
    CRITICAL = "CRITICAL"
    ATTENTION = "ATTENTION"
    NORMAL = "NORMAL"
    HEALTHY = "HEALTHY"

class ProductionSummary(BaseModel):
    target_kg: float = Field(..., description="Target production in KG")
    actual_kg: float = Field(..., description="Actual production in KG")
    loss_kg: float = Field(..., description="Production loss in KG")
    achievement_pct: float = Field(..., description="Achievement percentage")
    efficiency_pct: float = Field(..., description="Factory efficiency percentage")
    unit: str = "kg"

class ProductionVariance(BaseModel):
    target_kg: float
    actual_kg: float
    variance_kg: float
    variance_pct: float
    is_statistically_significant: bool = True
    display_note: str = ""

class ProductionTrendItem(BaseModel):
    label: str
    target_kg: float
    actual_kg: float
    loss_kg: float
    efficiency_pct: float

class LossContributor(BaseModel):
    category: str
    impact_kg: float
    percentage: float
    evidence: str

class PeriodComparisonMetric(BaseModel):
    metric: str
    current: str
    previous: str
    change_text: str
    change_pct: float
    trend: str  # 'down_bad' | 'up_bad' | 'up_good' | 'down_good' | 'neutral'

class MachineAttentionItem(BaseModel):
    machine_id: str
    machine_type: str
    section_id: str
    efficiency_pct: float
    loss_kg: float
    downtime_minutes: int
    change_pct: float
    status: PerformanceStatus
    primary_issue: str

class LowEfficiencyMachine(BaseModel):
    machine_id: str
    efficiency_pct: float
    factory_avg_pct: float
    gap_points: float
    historical_status: str

class AIInsightData(BaseModel):
    summary: str
    observations: List[str]
    contributors: List[str]
    recommended_investigation: List[str]
    evidence_found: List[str]
    confidence: str = "HIGH (EVIDENCE-BASED)"

class ImpactProjectionData(BaseModel):
    is_sufficient_data: bool = True
    daily_gap_kg: float
    projected_7d_gap_kg: float
    projected_30d_gap_kg: float
    assumptions_note: str
    insufficient_data_reason: Optional[str] = None

class RecommendedInvestigationData(BaseModel):
    priority: str = "HIGH"
    area: str
    machine_id: str
    observed_issue: str
    recommended_next_step: str

class ExecutiveSummaryData(BaseModel):
    factory_status: str
    main_issue: str
    affected_entity: str
    impact_kg: float
    recommended_action: str

class FactoryOverviewResponse(BaseModel):
    company_name: str = "Ashok Textiles"
    selected_unit: str = "All Units"
    selected_period: TimePeriod = TimePeriod.TODAY
    selected_comparison: ComparisonPeriod = ComparisonPeriod.PREVIOUS_DAY
    data_frequency: str = "DAILY"
    user_role: str = "SUPER_ADMIN"
    permitted_section: Optional[str] = None
    
    executive_summary: ExecutiveSummaryData
    production_summary: ProductionSummary
    variance: ProductionVariance
    trend: List[ProductionTrendItem]
    loss_contributors: List[LossContributor]
    period_comparison: List[PeriodComparisonMetric]
    machines_requiring_attention: List[MachineAttentionItem]
    low_efficiency_spotlight: LowEfficiencyMachine
    ai_insight: AIInsightData
    impact_projection: ImpactProjectionData
    recommended_investigation: RecommendedInvestigationData

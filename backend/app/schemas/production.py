from typing import List, Optional
from pydantic import BaseModel, Field

class MachineTypePerformanceItem(BaseModel):
    machine_type: str
    efficiency_pct: float
    loss_kg: float
    actual_kg: float
    target_kg: float
    status: str  # 'ATTENTION' | 'NORMAL' | 'HEALTHY'

class ProductionTrendPoint(BaseModel):
    date_label: str
    actual_kg: float
    target_kg: float
    gap_kg: float
    achievement_pct: Optional[float] = None

class LossReasonItem(BaseModel):
    rank: int
    category: str
    impact_kg: float
    percentage: float

class ShiftPerformanceItem(BaseModel):
    shift_name: str
    actual_kg: float
    target_kg: float
    achievement_pct: float

class ProductionFactorItem(BaseModel):
    name: str
    display_value: str
    direction: str  # 'UP' | 'DOWN'
    status: str     # 'CRITICAL' | 'ATTENTION' | 'HEALTHY' | 'NORMAL'

class ProductionComparisonData(BaseModel):
    reference_period: str = "Yesterday"
    reference_kg: float = 36100.0
    current_kg: float = 34620.0
    difference_kg: float = -1480.0
    difference_pct: float = -4.1
    main_reason: str = "Machine Downtime"

class AiProductionAnalysisData(BaseModel):
    summary: str
    affected_machine_type: str
    main_observed_factor: str
    recommended_action: str

class ProductionModuleResponse(BaseModel):
    company_name: str = "Ashok Textiles"
    selected_period: str = "THIS_MONTH"
    
    # Section 1: Top KPI
    actual_kg: float = 34620.0
    target_kg: float = 37000.0
    gap_kg: float = 2380.0
    achievement_pct: float = 93.6
    
    # Section 2: Trend
    trend: List[ProductionTrendPoint]
    
    # Section 3: Machine Type
    machine_type_performance: List[MachineTypePerformanceItem]
    
    # Section 4: Loss Reasons
    loss_reasons: List[LossReasonItem]

    # Section 5: Shift Performance
    shift_performance: List[ShiftPerformanceItem]

    # Section 6: Production Factors
    production_factors: List[ProductionFactorItem]

    # Legacy fields maintained for backward compatibility
    spotlight_machine_type: str = "N/A"
    spotlight_efficiency_pct: float = 0.0
    spotlight_factory_avg_gap: float = 0.0
    spotlight_loss_kg: float = 0.0
    is_reconciled: bool = True
    data_quality_warning: Optional[str] = None
    comparison: ProductionComparisonData
    ai_analysis: AiProductionAnalysisData

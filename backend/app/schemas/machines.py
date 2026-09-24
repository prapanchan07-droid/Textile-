from typing import List, Optional
from pydantic import BaseModel

class MachinePerformanceItem(BaseModel):
    machine_id: str
    machine_type: str
    actual_kg: float
    target_kg: float
    efficiency_pct: float
    loss_kg: float
    downtime_min: int
    status: str  # 'CRITICAL' | 'ATTENTION' | 'NORMAL'
    main_issue: str

class SpotlightMachine(BaseModel):
    machine_id: str
    machine_type: str
    loss_kg: float
    efficiency_pct: float
    downtime_min: int
    main_issue: str

class DowntimeKpi(BaseModel):
    total_downtime_min: int
    unplanned_downtime_min: int
    planned_downtime_min: int
    stoppage_count: int

class DowntimeReasonItem(BaseModel):
    category: str
    downtime_min: int
    percentage: float

class MachineTrendPoint(BaseModel):
    date_label: str
    efficiency_pct: float
    loss_kg: float

class MachineDetailData(BaseModel):
    machine_id: str
    machine_type: str
    actual_kg: float
    target_kg: float
    efficiency_pct: float
    loss_kg: float
    total_downtime_min: int
    stoppage_count: int
    main_reason: str
    last_maintenance: str
    next_maintenance: str
    recent_event: str
    power_events: int
    power_downtime_min: int
    quality_status: str

class MachinesModuleResponse(BaseModel):
    company_name: str = "Ashok Textiles"
    period: str = "THIS_MONTH"
    selected_machine_type: str = "ALL"
    selected_machine_id: str = "ALL"
    machine_types: List[str]
    all_machines: List[MachinePerformanceItem]
    spotlight_machine: SpotlightMachine
    downtime_kpis: DowntimeKpi
    downtime_reasons: List[DowntimeReasonItem]
    machine_trend: List[MachineTrendPoint]
    machine_trends_by_id: Optional[dict] = None
    machine_detail: Optional[MachineDetailData] = None

from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class MachineMasterOption(BaseModel):
    machine_id: str
    machine_type: str
    section: str

class MachineMetricValue(BaseModel):
    machine_id: str
    machine_type: str
    value: float
    formatted_value: str
    unit: str
    status: str # 'CRITICAL' | 'ATTENTION' | 'NORMAL'
    variance_vs_reference: Optional[float] = None
    variance_label: Optional[str] = None

class MultiMetricRow(BaseModel):
    metric_name: str
    unit: str
    values: Dict[str, str] # e.g. {"V-09": "84.2%", "V-05": "88.1%"}

class HeadToHeadMetric(BaseModel):
    metric_key: str
    metric_name: str
    unit: str
    machine1_value: float
    machine1_formatted: str
    machine2_value: float
    machine2_formatted: str
    delta_text: str
    leader_machine_id: Optional[str] = None

class ComparisonInsightData(BaseModel):
    summary_text: str
    key_observations: List[str]

class MachineComparisonResponse(BaseModel):
    company_name: str = "Ashok Textiles"
    selected_period: str
    selected_metric: str
    selected_machine_type: str
    selected_machine_ids: List[str]
    available_machine_types: List[str]
    all_master_machines: List[MachineMasterOption]
    
    # Baseline/Reference
    reference_type: str
    reference_value: float
    reference_formatted: str
    
    # Comparison results
    primary_metrics: List[MachineMetricValue]
    multi_metric_matrix: List[MultiMetricRow]
    head_to_head: Optional[List[HeadToHeadMetric]] = None
    insight: ComparisonInsightData

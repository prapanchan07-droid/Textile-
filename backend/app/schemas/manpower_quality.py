from typing import List, Optional
from pydantic import BaseModel

class ManpowerSummary(BaseModel):
    required: int
    available: int
    shortage: int
    attendance_pct: float

class DepartmentManpowerItem(BaseModel):
    department: str
    required: int
    available: int
    gap: int
    attendance_pct: float

class ManpowerTrendPoint(BaseModel):
    date_label: str
    required: int
    available: int
    shortage: int
    attendance_pct: float

class QualityStatusData(BaseModel):
    status: str  # 'NORMAL' | 'ATTENTION' | 'CRITICAL'
    samples_tested: int
    pass_rate_pct: float
    defect_rate_pct: float
    main_issue: str

class QualityParameterItem(BaseModel):
    parameter: str
    label: str
    value: float
    limit: float
    unit: str
    status: str  # 'NORMAL' | 'ATTENTION' | 'OUT OF LIMIT'

class QualityTrendPoint(BaseModel):
    date_label: str
    value: float
    limit: float

class QualityMachineItem(BaseModel):
    machine_process: str
    quality_issue: str
    current_value: float
    limit: float
    unit: str
    status: str  # 'NORMAL' | 'ATTENTION' | 'OUT OF LIMIT'

class AttentionItem(BaseModel):
    severity: str  # 'HIGH' | 'MEDIUM' | 'LOW'
    title: str
    detail: str

class ManpowerQualityModuleResponse(BaseModel):
    company_name: str = "Ashok Textiles"
    period: str = "THIS_MONTH"
    manpower_summary: ManpowerSummary
    department_gaps: List[DepartmentManpowerItem]
    manpower_trend: List[ManpowerTrendPoint]
    quality_status: QualityStatusData
    quality_parameters: List[QualityParameterItem]
    quality_trends_by_param: dict
    quality_issues_by_machine: List[QualityMachineItem]
    needs_attention: List[AttentionItem]

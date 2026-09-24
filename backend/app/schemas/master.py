from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

class DataFrequency(str, Enum):
    SHIFT = "SHIFT"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"

class StandardIdentifiers(BaseModel):
    date: Optional[str] = Field(None, description="ISO date YYYY-MM-DD")
    timestamp: Optional[str] = Field(None, description="ISO timestamp")
    shift: Optional[str] = Field(None, description="Shift identifier e.g., Shift A, Shift B, Shift 1")
    unit_id: Optional[str] = Field(None, description="Unit I, Unit II")
    department_id: Optional[str] = Field(None, description="Spinning, Sizing, Weaving, etc.")
    section_id: Optional[str] = Field(None, description="Section A, Section B")
    process_id: Optional[str] = Field(None, description="Carding, Draw Frame, Simplex, Weaving, Sizing")
    machine_type_id: Optional[str] = Field(None, description="Ring Frame, Vortex, Airjet, Toyota")
    machine_id: Optional[str] = Field(None, description="SMX-03, V-05, etc.")
    product_id: Optional[str] = None
    batch_id: Optional[str] = None
    order_id: Optional[str] = None
    employee_id: Optional[str] = None

class RawVsDerivedSchema(BaseModel):
    raw_target: float = Field(..., description="Target production from report")
    raw_actual: float = Field(..., description="Actual production recorded")
    
    @property
    def derived_production_loss(self) -> float:
        return max(0.0, self.raw_target - self.raw_actual)

    @property
    def derived_achievement_percentage(self) -> float:
        if self.raw_target <= 0:
            return 0.0
        return round((self.raw_actual / self.raw_target) * 100.0, 2)

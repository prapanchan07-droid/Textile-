from typing import Optional, List
from fastapi import APIRouter, Query
from app.schemas.common import StandardResponse
from app.schemas.machine_comparison import MachineComparisonResponse
from app.services.machine_comparison_service import machine_comparison_service

router = APIRouter()

@router.get("/machine-comparison", response_model=StandardResponse[MachineComparisonResponse])
def get_machine_comparison_telemetry(
    machines: Optional[List[str]] = Query(None, description="List of selected machine IDs to compare e.g. V-09, V-05"),
    metric: str = Query("EFFICIENCY", description="Metric key to compare: EFFICIENCY, PRODUCTION, PRODUCTION_LOSS, DOWNTIME, UTILIZATION, ENERGY_PER_KG, QUALITY"),
    period: str = Query("TODAY", description="Time period filter: TODAY, YESTERDAY, THIS_MONTH, LAST_7_DAYS"),
    machine_type: str = Query("ALL", description="Machine type filter: ALL, Vortex, Airjet, Ring Frame, Simplex"),
    reference: str = Query("FACTORY_AVG", description="Reference baseline: FACTORY_AVG, DEPT_AVG, TARGET, NONE")
):
    """
    Get dynamic interactive machine comparison workspace telemetry.
    Supports filtering by custom selected machines, period, machine type, metric, and baseline overlays.
    """
    data = machine_comparison_service.get_comparison_data(
        selected_ids=machines,
        metric=metric,
        period=period,
        machine_type_filter=machine_type,
        reference_type=reference
    )
    return StandardResponse(success=True, data=data)

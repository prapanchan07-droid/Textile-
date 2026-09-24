from fastapi import APIRouter, Query
from app.schemas.common import StandardResponse
from app.schemas.machines import MachinesModuleResponse
from app.services.machines_service import MachinesService

router = APIRouter(prefix="/machines", tags=["Machines & Downtime Module"])

@router.get("", response_model=StandardResponse[MachinesModuleResponse])
def get_machines_module_data(
    period: str = Query("THIS_MONTH", description="Period filter: TODAY, SEVEN_DAYS, THIS_MONTH"),
    machine_type: str = Query("ALL", description="Machine Type filter e.g. Vortex, Airjet, Ring Frame, Simplex"),
    machine_id: str = Query("ALL", description="Machine ID filter e.g. V-09, V-05, SMX-03")
):
    data = MachinesService.get_machines_data(
        period=period,
        machine_type=machine_type,
        machine_id=machine_id
    )
    return StandardResponse(success=True, data=data)

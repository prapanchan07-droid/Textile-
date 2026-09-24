from fastapi import APIRouter, Query
from app.schemas.common import StandardResponse
from app.schemas.decision_center import DecisionCenterData
from app.services.decision_center_service import decision_center_service

router = APIRouter()

@router.get("/decision-center", response_model=StandardResponse[DecisionCenterData])
def get_decision_center_telemetry(
    period: str = Query("TODAY", description="Time period filter: TODAY, SHIFT, THIS_WEEK, THIS_MONTH"),
    comparison: str = Query("PREVIOUS_DAY", description="Comparison period"),
    unit: str = Query("All Units", description="Factory unit filter"),
    user_role: str = Query("SUPER_ADMIN", description="Role access level"),
    section_access: str = Query("ALL", description="Permitted section access")
):
    """
    Get Decision Center executive telemetry & action recommendations.
    Synthesizes findings across Production, Machines, Downtime, Manpower, Quality, and Revenue.
    """
    data = decision_center_service.get_decision_center(
        period=period,
        comparison=comparison,
        unit=unit,
        user_role=user_role,
        section_access=section_access
    )
    return StandardResponse(success=True, data=data)

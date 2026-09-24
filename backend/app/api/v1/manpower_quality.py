from fastapi import APIRouter, Query
from app.schemas.common import StandardResponse
from app.schemas.manpower_quality import ManpowerQualityModuleResponse
from app.services.manpower_quality_service import ManpowerQualityService

router = APIRouter(prefix="/manpower-quality", tags=["Manpower & Quality Module"])

@router.get("", response_model=StandardResponse[ManpowerQualityModuleResponse])
def get_manpower_quality_module_data(
    period: str = Query("THIS_MONTH", description="Period filter: TODAY, SEVEN_DAYS, THIS_MONTH")
):
    data = ManpowerQualityService.get_manpower_quality_data(period=period)
    return StandardResponse(success=True, data=data)

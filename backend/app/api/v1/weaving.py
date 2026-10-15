from fastapi import APIRouter, Query
from app.schemas.common import StandardResponse
from app.schemas.weaving import WeavingModuleResponse
from app.services.weaving_service import WeavingService

router = APIRouter(prefix="/weaving", tags=["Weaving Module (mock data)"])


@router.get("", response_model=StandardResponse[WeavingModuleResponse])
def get_weaving_module_data(
    period: str = Query("TODAY", description="TODAY, YESTERDAY, LAST_7_DAYS, THIS_MONTH")
):
    return StandardResponse(success=True, data=WeavingService.get_weaving_data(period=period))

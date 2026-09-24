from fastapi import APIRouter, Query
from app.schemas.common import StandardResponse
from app.schemas.revenue_loss import RevenueLossModuleResponse
from app.services.revenue_loss_service import RevenueLossService

router = APIRouter(prefix="/revenue-loss", tags=["Revenue & Loss Module"])

@router.get("", response_model=StandardResponse[RevenueLossModuleResponse])
def get_revenue_loss_module_data(
    period: str = Query("THIS_MONTH", description="Period filter: TODAY, SEVEN_DAYS, THIS_MONTH")
):
    data = RevenueLossService.get_revenue_loss_data(period=period)
    return StandardResponse(success=True, data=data)

from typing import Optional
from fastapi import APIRouter, Query, Header
from app.schemas.common import StandardResponse
from app.schemas.overview import (
    FactoryOverviewResponse,
    TimePeriod,
    ComparisonPeriod,
    ProductionSummary,
    LossContributor,
    MachineAttentionItem,
    AIInsightData,
    ImpactProjectionData
)
from app.services.overview_service import OverviewService
from typing import List

router = APIRouter(prefix="/overview", tags=["Factory Overview"])

@router.get("", response_model=StandardResponse[FactoryOverviewResponse])
def get_factory_overview(
    period: TimePeriod = Query(TimePeriod.TODAY, description="Time period filter"),
    comparison: ComparisonPeriod = Query(ComparisonPeriod.PREVIOUS_DAY, description="Comparison period filter"),
    unit_id: Optional[str] = Query(None, description="Optional Unit filter"),
    x_user_role: Optional[str] = Header("SUPER_ADMIN", alias="X-User-Role"),
    x_section_access: Optional[str] = Header("ALL", alias="X-Section-Access")
):
    overview_data = OverviewService.get_factory_overview(
        period=period,
        comparison=comparison,
        unit_id=unit_id,
        user_role=x_user_role or "SUPER_ADMIN",
        section_access=x_section_access or "ALL"
    )
    return StandardResponse(success=True, data=overview_data)

@router.get("/production-summary", response_model=StandardResponse[ProductionSummary])
def get_production_summary():
    overview = OverviewService.get_factory_overview()
    return StandardResponse(success=True, data=overview.production_summary)

@router.get("/loss-contributors", response_model=StandardResponse[List[LossContributor]])
def get_loss_contributors():
    overview = OverviewService.get_factory_overview()
    return StandardResponse(success=True, data=overview.loss_contributors)

@router.get("/machine-attention", response_model=StandardResponse[List[MachineAttentionItem]])
def get_machine_attention(
    x_section_access: Optional[str] = Header("ALL", alias="X-Section-Access")
):
    overview = OverviewService.get_factory_overview(section_access=x_section_access)
    return StandardResponse(success=True, data=overview.machines_requiring_attention)

@router.get("/ai-insight", response_model=StandardResponse[AIInsightData])
def get_ai_insight():
    overview = OverviewService.get_factory_overview()
    return StandardResponse(success=True, data=overview.ai_insight)

@router.get("/impact-projection", response_model=StandardResponse[ImpactProjectionData])
def get_impact_projection():
    overview = OverviewService.get_factory_overview()
    return StandardResponse(success=True, data=overview.impact_projection)

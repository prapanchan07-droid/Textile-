from typing import Optional
from fastapi import APIRouter, Query
from app.schemas.common import StandardResponse
from app.schemas.production import ProductionModuleResponse
from app.services.production_service import ProductionService
from app.db.session import SessionLocal
from app.models.ingestion import ProductionRecord

router = APIRouter(prefix="/production", tags=["Production Module"])

@router.get("", response_model=StandardResponse[ProductionModuleResponse])
def get_production_module_data(
    period: str = Query("THIS_MONTH", description="Period filter e.g. TODAY, SEVEN_DAYS, THIS_MONTH"),
    date: Optional[str] = Query(None, description="Date filter format YYYY-MM-DD"),
    unit: Optional[str] = Query(None, description="Unit filter e.g. Unit I, Unit II, All Units")
):
    data = ProductionService.get_production_data(period=period, target_date=date, unit=unit)
    return StandardResponse(success=True, data=data)

@router.get("/debug")
def get_production_debug_data(
    date: Optional[str] = Query(None),
    unit: Optional[str] = Query(None)
):
    db = SessionLocal()
    try:
        data = ProductionService.get_production_data(target_date=date, unit=unit)
        all_recs = db.query(ProductionRecord).all()
        return {
            "selected_date_records_count": len([r for r in all_recs if date is None or r.report_date == date]),
            "total_records_in_db": len(all_recs),
            "response_actual_kg": data.actual_kg,
            "response_target_kg": data.target_kg,
            "response_gap_kg": data.gap_kg,
            "shift_performance": data.shift_performance,
            "shift_sum_actual": sum(s.actual_kg for s in (data.shift_performance or [])),
            "shift_sum_target": sum(s.target_kg for s in (data.shift_performance or [])),
            "shift_sum_gap": sum(max(0.0, s.target_kg - s.actual_kg) for s in (data.shift_performance or [])),
            "is_math_reconciled": (
                round(data.actual_kg, 1) == round(sum(s.actual_kg for s in (data.shift_performance or [])), 1) and
                round(data.target_kg, 1) == round(sum(s.target_kg for s in (data.shift_performance or [])), 1) and
                round(data.gap_kg, 1) == round(sum(max(0.0, s.target_kg - s.actual_kg) for s in (data.shift_performance or [])), 1)
            )
        }
    finally:
        db.close()

@router.get("/lineage")
def get_production_lineage_data(
    date: Optional[str] = Query(None),
    unit: Optional[str] = Query(None)
):
    lineage = ProductionService.get_production_lineage(target_date=date, unit=unit)
    return StandardResponse(success=True, data=lineage)


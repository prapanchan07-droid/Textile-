from fastapi import APIRouter
from app.core.config import settings
from app.db.session import check_db_connection
from app.schemas.common import StandardResponse, HealthResponseData

router = APIRouter()

@router.get("/health", response_model=StandardResponse[HealthResponseData])
def health_check():
    db_health = check_db_connection()
    overall_status = "healthy" if db_health.get("status") == "healthy" else "degraded"
    
    return StandardResponse(
        success=True,
        data=HealthResponseData(
            status=overall_status,
            project_name=settings.PROJECT_NAME,
            company=settings.COMPANY_NAME,
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
            database=db_health,
            active_module="MODULE_01 - Project Foundation"
        )
    )

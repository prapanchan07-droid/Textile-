from fastapi import APIRouter
from app.api.v1 import health, overview, production, machines, manpower_quality, revenue_loss, decision_center, machine_comparison, ingestion

api_router = APIRouter()
api_router.include_router(health.router, tags=["System & Health"])
api_router.include_router(ingestion.router)
api_router.include_router(overview.router)
api_router.include_router(production.router)
api_router.include_router(machines.router)
api_router.include_router(manpower_quality.router)
api_router.include_router(revenue_loss.router)
api_router.include_router(decision_center.router)
api_router.include_router(machine_comparison.router)

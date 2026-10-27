from fastapi import APIRouter, Depends

from app.api.deps import require_roles
from app.api.v1 import auth, health, ingestion
from app.core.roles import Role

api_router = APIRouter()

# Public: liveness for Docker/load balancers, and the sign-in endpoints themselves.
api_router.include_router(health.router, tags=["System & Health"])
api_router.include_router(auth.router)

# Report ingestion: admin only.
api_router.include_router(ingestion.router, dependencies=[Depends(require_roles(Role.ADMIN))])

from fastapi import APIRouter, Depends

from app.api.deps import require_roles
from app.api.v1 import (
    auth, decision_center, health, ingestion, machine_comparison, machines, manpower_quality, overview, production, revenue_loss, weaving,
)
from app.core.roles import Role

api_router = APIRouter()

# Public: liveness for Docker/load balancers, and the sign-in endpoints themselves.
api_router.include_router(health.router, tags=["System & Health"])
api_router.include_router(auth.router)

# Weaving: signed-in users; each route narrows to the roles whose menu includes that section (see api/v1/weaving.py).
api_router.include_router(weaving.router)

# Report ingestion and the pre-weaving factory modules hold whole-factory data (uploads, production, revenue):
# owner and weaving manager only.
_management = [Depends(require_roles(Role.OWNER, Role.WEAVING_MANAGER))]
for _r in (ingestion, overview, production, machines, manpower_quality, revenue_loss, decision_center, machine_comparison):
    api_router.include_router(_r.router, dependencies=_management)

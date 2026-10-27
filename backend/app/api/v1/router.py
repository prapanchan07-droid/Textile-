from fastapi import APIRouter, Depends

from app.api.deps import require_roles
from app.api.v1 import auth, health
from app.api.v1.mill import alerts, analytics, imports, reports, work
from app.core.roles import Role

api_router = APIRouter()

# Public: liveness for Docker/load balancers, and the sign-in endpoints themselves.
api_router.include_router(health.router, tags=["System & Health"])
api_router.include_router(auth.router)

# Weaving platform: every route needs a signed-in user with a permitted role (enforced here, not only in the UI).
# Only ADMIN exists today; when roles are added, narrow individual routers or routes with require_roles(...).
_signed_in = [Depends(require_roles(Role.ADMIN))]
for _r in (analytics, imports, alerts, work, reports):
    api_router.include_router(_r.router, prefix="/mill", dependencies=_signed_in)

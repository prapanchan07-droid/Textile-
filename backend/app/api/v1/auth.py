from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.roles import ROLE_LABELS, Role
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, UserOut
from app.schemas.common import StandardResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _user_out(user: User) -> UserOut:
    role = Role(user.role)
    return UserOut(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        role=role.value,
        role_label=ROLE_LABELS[role],
    )


@router.post("/login", response_model=StandardResponse[LoginResponse])
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username.strip().lower()).first()
    # Same message for unknown user and wrong password so usernames can't be probed.
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        raise UnauthorizedException("Wrong username or password")
    user.last_login_at = datetime.utcnow()
    db.commit()
    return StandardResponse(
        success=True,
        data=LoginResponse(
            access_token=create_access_token(user.id, user.role),
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=_user_out(user),
        ),
    )


@router.get("/me", response_model=StandardResponse[UserOut])
def me(user: User = Depends(get_current_user)):
    return StandardResponse(success=True, data=_user_out(user))

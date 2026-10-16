from typing import Callable, Iterable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.roles import ROLE_SECTIONS, Role
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise UnauthorizedException("Please sign in")
    payload = decode_access_token(creds.credentials)
    if not payload:
        raise UnauthorizedException("Your session has expired. Please sign in again")
    user = db.get(User, payload.get("sub"))
    if user is None or not user.is_active:
        raise UnauthorizedException("This account is no longer active")
    return user


def require_roles(*roles: Role) -> Callable[..., User]:
    allowed: Iterable[str] = {r.value for r in roles}

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise ForbiddenException("Your role does not have access to this")
        return user

    return checker


def require_section(section: str) -> Callable[..., User]:
    """Allow only roles whose weaving sections include `section` (the same table that drives the frontend menu)."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if section not in ROLE_SECTIONS[Role(user.role)]:
            raise ForbiddenException("Your role does not have access to this")
        return user

    return checker


def require_any_section(*sections: str) -> Callable[..., User]:
    """Allow roles whose menu includes at least one of these sections."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if not set(sections) & set(ROLE_SECTIONS[Role(user.role)]):
            raise ForbiddenException("Your role does not have access to this")
        return user

    return checker

"""
Roles. Only ADMIN exists for now; add new members (and labels) here when more roles are introduced.
"""
from enum import Enum
from typing import Dict, List


class Role(str, Enum):
    ADMIN = "ADMIN"


ROLE_LABELS: Dict[Role, str] = {
    Role.ADMIN: "Admin",
}

ALL_ROLES: List[Role] = list(Role)

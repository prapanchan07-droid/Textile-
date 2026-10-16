"""
Roles and the weaving pages each one may open.

The frontend builds its navigation and landing page from this table (via
``GET /auth/me``) and the API enforces it with ``require_roles``, so the two
cannot drift apart.
"""
from enum import Enum
from typing import Dict, List


class Role(str, Enum):
    OWNER = "OWNER"
    WEAVING_MANAGER = "WEAVING_MANAGER"
    SHIFT_SUPERVISOR = "SHIFT_SUPERVISOR"
    MAINTENANCE = "MAINTENANCE"
    QUALITY = "QUALITY"


ROLE_LABELS: Dict[Role, str] = {
    Role.OWNER: "Owner / MD",
    Role.WEAVING_MANAGER: "Weaving Manager",
    Role.SHIFT_SUPERVISOR: "Shift Supervisor",
    Role.MAINTENANCE: "Maintenance Engineer",
    Role.QUALITY: "Quality Controller",
}

# Weaving pages (frontend route slugs) each role may open; the first entry is the landing page.
# Each role gets pages of its own as well as shared ones, because their decisions differ:
#   owner       money, delivery promises, customers, approvals
#   manager     the whole department: production, stoppages, machines, people, planning
#   supervisor  the shift in progress: floor, hand-over, who is present
#   maintenance machines, health, planned and breakdown work
#   quality     defects, yarn lots, shift-to-shift differences
ROLE_SECTIONS: Dict[Role, List[str]] = {
    Role.OWNER: ["owner", "orders", "scheduler", "insights", "compare", "actions"],
    Role.WEAVING_MANAGER: ["command", "production", "stoppages", "machines", "workforce", "orders", "scheduler", "insights", "compare", "actions"],
    Role.SHIFT_SUPERVISOR: ["cockpit", "handover", "stoppages", "machines", "workforce", "actions"],
    Role.MAINTENANCE: ["maintenance", "machines", "stoppages", "actions"],
    Role.QUALITY: ["quality", "insights", "compare", "actions"],
}

# Roles that may see rupee figures and approve plans
FINANCIAL_ROLES = (Role.OWNER, Role.WEAVING_MANAGER)

ALL_ROLES: List[Role] = list(Role)

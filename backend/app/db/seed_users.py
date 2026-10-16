import uuid

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.core.roles import Role
from app.core.security import hash_password
from app.models.user import User

DEMO_PASSWORD = "Ashok@2026"

DEMO_USERS = [
    ("owner", "Gokul Ashok", Role.OWNER),
    ("manager", "Ramesh Kumar", Role.WEAVING_MANAGER),
    ("supervisor", "Selvam P", Role.SHIFT_SUPERVISOR),
    ("maintenance", "Karthik R", Role.MAINTENANCE),
    ("quality", "Priya S", Role.QUALITY),
]


def seed_demo_users(db: Session) -> None:
    if not settings.demo_users_enabled:
        return
    existing = {u.username for u in db.query(User.username).all()}
    added = 0
    for username, full_name, role in DEMO_USERS:
        if username in existing:
            continue
        db.add(User(id=str(uuid.uuid4()), username=username, full_name=full_name, role=role.value, password_hash=hash_password(DEMO_PASSWORD)))
        added += 1
    if added:
        db.commit()
        logger.info(f"Seeded {added} demo user(s).")

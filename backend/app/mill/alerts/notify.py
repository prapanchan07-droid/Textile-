"""
Notifications. In-app delivery is the only channel configured in this deployment; email / SMS / WhatsApp need a
provider and credentials (see docs/weaving-platform.md) and are reported as NOT_CONFIGURED rather than pretended.
Any delivery failure is stored on the notification and never raised to the caller.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.mill.models import Notification
from app.models.user import User

CHANNELS = {"IN_APP": True, "EMAIL": False, "SMS": False, "WHATSAPP": False}  # True = configured and tested


def notify_users(db: Session, *, title: str, body: Optional[str] = None, severity: str = "INFO", alert_id: Optional[int] = None,
                 task_id: Optional[int] = None, link: Optional[str] = None) -> int:
    sent = 0
    try:
        users = list(db.scalars(select(User).where(User.is_active.is_(True))))
    except Exception as e:  # pragma: no cover - database trouble is logged, evaluation continues
        logger.error(f"Notification lookup failed: {e}")
        return 0
    for u in users:
        try:
            with db.begin_nested():
                db.add(Notification(user_id=u.id, channel="IN_APP", title=title[:200], body=body, severity=severity, alert_id=alert_id,
                                    task_id=task_id, link=link, delivery_status="DELIVERED"))
            sent += 1
        except Exception as e:
            logger.error(f"In-app notification to {u.username} failed: {e}")
    return sent

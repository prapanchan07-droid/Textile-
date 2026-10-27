"""Audit trail for changes people make (assignments, rules, tasks, report publication, incident resolution)."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable, Optional

from sqlalchemy.orm import Session

from app.mill.models import AuditLog


def snapshot(obj: Any, fields: Iterable[str]) -> dict:
    out = {}
    for f in fields:
        v = getattr(obj, f, None)
        out[f] = v.isoformat() if isinstance(v, (date, datetime)) else v
    return out


def record(db: Session, actor_id: Optional[str], action: str, entity: str, entity_id: Any,
           before: Optional[dict] = None, after: Optional[dict] = None) -> None:
    if before is not None and after is not None:
        changed = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
        if not changed:
            return
        before = {k: before.get(k) for k in changed}
        after = {k: after.get(k) for k in changed}
    db.add(AuditLog(actor_id=actor_id, action=action, entity=entity, entity_id=None if entity_id is None else str(entity_id),
                    before=before, after=after))

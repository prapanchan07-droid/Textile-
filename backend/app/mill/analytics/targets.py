"""Configured production targets. The most specific target that applies on a date wins: loom > group > category > mill."""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.mill.models import ProductionTarget

ORDER = {"LOOM": 0, "GROUP": 1, "CATEGORY": 2, "MILL": 3}


class Targets:
    def __init__(self, db: Session, metric: str, on_from: Optional[date] = None, on_to: Optional[date] = None):
        q = select(ProductionTarget).where(ProductionTarget.metric == metric)
        if on_to:
            q = q.where(ProductionTarget.effective_from <= on_to)
        if on_from:
            q = q.where(or_(ProductionTarget.effective_to.is_(None), ProductionTarget.effective_to >= on_from))
        self.rows: List[ProductionTarget] = sorted(db.scalars(q), key=lambda t: (ORDER[t.scope], -t.effective_from.toordinal()))

    def __bool__(self) -> bool:
        return bool(self.rows)

    def value(self, on: date, loom_code: str, category: str, group_id: Optional[int]) -> Optional[float]:
        refs: Dict[str, Optional[str]] = {"LOOM": loom_code, "GROUP": str(group_id) if group_id else None, "CATEGORY": category, "MILL": None}
        for t in self.rows:
            if t.effective_from > on or (t.effective_to and t.effective_to < on):
                continue
            if t.scope == "MILL" or (refs[t.scope] is not None and t.scope_ref == refs[t.scope]):
                return t.value
        return None

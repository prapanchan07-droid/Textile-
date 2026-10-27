"""Shared query parameters and helpers for the weaving API."""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationException
from app.mill import constants as C
from app.mill.analytics.records import Filters, resolve_period
from app.schemas.common import StandardResponse


def ok(data) -> StandardResponse:
    return StandardResponse(success=True, data=data)


def _split(v: Optional[str]) -> List[str]:
    return [x.strip().upper() for x in v.split(",") if x.strip()] if v else []


class FilterParams:
    """period=latest|7d|30d|month|custom (custom needs date_from/date_to); plus shift, category, loom, group, style, source."""

    def __init__(
        self,
        period: str = Query("30d", pattern="^(latest|7d|30d|month|custom)$"),
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        shift: Optional[str] = Query(None, description="Comma list of A,B,C"),
        category: Optional[str] = Query(None, description="Comma list of TY,TS,SZ"),
        loom_id: Optional[int] = None,
        group_id: Optional[int] = None,
        style: Optional[str] = None,
        source: str = Query("auto", pattern="^(auto|MILL_REPORT|MACHINE_EXPORT)$"),
    ):
        self.period, self.date_from, self.date_to = period, date_from, date_to
        self.shifts = _split(shift)
        self.categories = _split(category)
        if any(s not in C.SHIFTS for s in self.shifts) or any(c not in C.CATEGORIES for c in self.categories):
            raise ValidationException("Unknown shift or category")
        if period == "custom" and (not date_from or not date_to or date_from > date_to):
            raise ValidationException("A custom period needs date_from <= date_to")
        self.loom_id, self.group_id, self.style, self.source = loom_id, group_id, style, source

    def filters(self, db: Session) -> Filters:
        p = resolve_period(db, self.period, self.date_from, self.date_to)
        return Filters(date_from=p["date_from"], date_to=p["date_to"], shifts=self.shifts, categories=self.categories,
                       loom_ids=[self.loom_id] if self.loom_id else [], group_id=self.group_id, style=self.style, source=self.source)


def paginate(db: Session, q, page: int, page_size: int, serialize):
    total = db.scalar(select(func.count()).select_from(q.order_by(None).subquery()))
    items = [serialize(x) for x in db.scalars(q.offset((page - 1) * page_size).limit(page_size))]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


Page = Query(1, ge=1)
PageSize = Query(50, ge=1, le=500)

"""Read-only analytics: command center, looms, production, comparison, findings, energy, metric definitions."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.mill.common import FilterParams, ok
from app.core.exceptions import NotFoundException
from app.db.session import get_db
from app.mill import constants as C
from app.mill.analytics import metrics as M
from app.mill.analytics import pages
from app.mill.analytics.findings import find
from app.mill.models import Group, Loom, ShiftProduction, Style

router = APIRouter(tags=["Weaving analytics"])


@router.get("/meta")
def meta(db: Session = Depends(get_db)):
    """Filter options and the data range, so pages never offer filters that match nothing."""
    first, last = db.execute(select(func.min(ShiftProduction.prod_date), func.max(ShiftProduction.prod_date))).one()
    return ok(pages.jsonable({
        "categories": [{"code": k, "name": v} for k, v in C.CATEGORIES.items()],
        "shifts": [{"code": s, "start": C.SHIFT_TIMES[s][0].strftime("%H:%M"), "end": C.SHIFT_TIMES[s][1].strftime("%H:%M")} for s in C.SHIFTS],
        "styles": [{"code": s.code, "description": s.description} for s in db.scalars(select(Style).order_by(Style.code))],
        "groups": [{"id": g.id, "code": g.code, "name": g.name} for g in db.scalars(select(Group).where(Group.is_active.is_(True)).order_by(Group.code))],
        "looms": [{"id": l.id, "code": l.code, "category": l.category} for l in db.scalars(select(Loom).order_by(Loom.category, Loom.loom_no))],
        "data_range": {"first": first, "last": last},
        "freshness": pages.freshness(db),
    }))


@router.get("/dashboard")
def dashboard(p: FilterParams = Depends(), db: Session = Depends(get_db)):
    return ok(pages.command_center(db, p.filters(db)))


@router.get("/looms")
def looms(p: FilterParams = Depends(), db: Session = Depends(get_db)):
    return ok(pages.loom_grid(db, p.filters(db)))


@router.get("/looms/{loom_id}")
def loom(loom_id: int, p: FilterParams = Depends(), db: Session = Depends(get_db)):
    l = db.get(Loom, loom_id)
    if l is None:
        raise NotFoundException("Loom not found")
    return ok(pages.loom_detail(db, l, p.filters(db)))


@router.get("/production")
def production(p: FilterParams = Depends(), db: Session = Depends(get_db)):
    return ok(pages.production(db, p.filters(db)))


@router.get("/compare")
def compare(dimension: str = Query("loom", pattern="^(loom|shift|style|category|date|group|width)$"), p: FilterParams = Depends(),
            db: Session = Depends(get_db)):
    return ok(pages.compare(db, p.filters(db), dimension))


@router.get("/findings")
def findings(limit: int = Query(50, ge=1, le=200), p: FilterParams = Depends(), db: Session = Depends(get_db)):
    f = p.filters(db)
    return ok(pages.jsonable({"period": {"date_from": f.date_from, "date_to": f.date_to}, "findings": find(db, f, limit)}))


@router.get("/energy")
def energy(p: FilterParams = Depends(), db: Session = Depends(get_db)):
    return ok(pages.energy(db, p.filters(db)))


@router.get("/definitions")
def definitions():
    return ok([m.__dict__ for m in M.DEFINITIONS])

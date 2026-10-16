"""One analysis run: the clock, the mill calendar, reference data and lazily loaded fact rows."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from functools import cached_property
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.weaving import models as m
from app.weaving.analytics import facts
from app.weaving.analytics.calendar import MillCalendar, ReportWindow, ShiftDef

LENS_DAYS = 14  # investigations look at the last 14 production days...
BASELINE_DAYS = 14  # ...and compare with the 14 days before that
HISTORY_DAYS = 28  # change-point search for a single loom


def load_calendar(db: Session) -> MillCalendar:
    shifts = [ShiftDef(s.id, s.code, s.name, s.start_time, s.end_time, s.sort_order) for s in db.scalars(select(m.WvShift).order_by(m.WvShift.sort_order))]
    return MillCalendar(settings.MILL_TIMEZONE, shifts) if shifts else MillCalendar(settings.MILL_TIMEZONE)


class AnalysisContext:
    def __init__(self, db: Session, now: Optional[datetime] = None, period: str = "TODAY", lens_days: int = LENS_DAYS):
        self.db = db
        self.now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        self.cal = load_calendar(db)
        self.window: ReportWindow = self.cal.window(period, self.now)
        self.previous: ReportWindow = self.cal.previous(self.window, self.now)
        self.today: date = self.cal.production_day(self.now)
        self.lens_days = max(3, min(lens_days, 60))
        self.lens_end: date = self.window.end_date
        self.lens_start: date = self.lens_end - timedelta(days=self.lens_days - 1)
        self.baseline_end: date = self.lens_start - timedelta(days=1)
        self.baseline_start: date = self.baseline_end - timedelta(days=BASELINE_DAYS - 1)
        self.hist_days = max(HISTORY_DAYS, self.window.days + BASELINE_DAYS, self.lens_days + BASELINE_DAYS)

    @cached_property
    def refs(self) -> facts.Refs:
        return facts.load_refs(self.db)

    @property
    def hist_start(self) -> date:
        return self.window.end_date - timedelta(days=self.hist_days - 1)

    @cached_property
    def lens_window(self) -> ReportWindow:
        return self.cal.window_for_dates(self.lens_start, self.lens_end, self.now)

    # --- fact rows, each loaded once ---------------------------------------------------------

    @cached_property
    def prod_hist(self) -> List[facts.ProdRow]:
        """Production rows for the whole history span (also contains the report window and the previous window)."""
        start = min(self.hist_start, self.previous.start_date)
        return facts.load_production(self.db, start, self.window.end_date)

    def prod_between(self, start: date, end: date) -> List[facts.ProdRow]:
        return [r for r in self.prod_hist if start <= r.shift_date <= end]

    @cached_property
    def stops_window(self) -> List[facts.StopRow]:
        return facts.load_stops(self.db, self.window, self.now)

    @cached_property
    def stops_previous(self) -> List[facts.StopRow]:
        return facts.load_stops(self.db, self.previous, self.now)

    @cached_property
    def stops_hist(self) -> List[facts.StopRow]:
        hist = self.cal.window_for_dates(min(self.hist_start, self.previous.start_date), self.window.end_date, self.now)
        return facts.load_stops(self.db, hist, self.now)

    def stops_between(self, start: date, end: date) -> List[facts.StopRow]:
        return [r for r in self.stops_hist if start <= r.shift_date <= end]

    @cached_property
    def insp_hist(self) -> List[facts.InspRow]:
        return facts.load_inspections(self.db, min(self.hist_start, self.previous.start_date), self.window.end_date)

    @cached_property
    def defects_hist(self) -> List[facts.DefectRow]:
        return facts.load_defects(self.db, min(self.hist_start, self.previous.start_date), self.window.end_date)

    @cached_property
    def sensor_days(self) -> List[facts.SensorDay]:
        return facts.load_sensor_days(self.db, self.hist_start, self.window.end_date)

    def insp_between(self, start: date, end: date):
        return [r for r in self.insp_hist if start <= r.shift_date <= end], [d for d in self.defects_hist if start <= d.shift_date <= end]


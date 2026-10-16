"""Small hand-built fixtures with known numbers, so formulas can be checked against arithmetic done by hand."""
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from app.weaving import models as m
from app.weaving.seed.reference import ensure_reference_data

UTC = timezone.utc
FIXED_NOW = datetime(2026, 10, 15, 12, 0, tzinfo=UTC)  # 17:30 IST on production day 2026-10-15


class World:
    """One loom, one style, the standard shifts and reasons."""

    def __init__(self, db, rpm: int = 800, ppi: float = 50, target_eff: float = 90):
        ensure_reference_data(db)
        db.flush()
        self.db = db
        self.shift = {s.code: s for s in db.query(m.WvShift)}
        self.reason = {r.code: r for r in db.query(m.WvStopReason)}
        self.dtype = {d.code: d for d in db.query(m.WvDefectType)}
        self.loom = m.WvLoom(loom_code="T-01", loom_type="Airjet", rated_rpm=rpm, data_origin="LIVE")
        self.style = m.WvStyle(style_code="TS-1", fabric_name="Test fabric", ppi=ppi, target_efficiency_pct=target_eff, rate_per_m=100, std_cost_per_m=80, variable_cost_per_m=60, data_origin="LIVE")
        db.add_all([self.loom, self.style])
        db.flush()

    def reading(self, start: datetime, running_s: int = 3600, picks: Optional[int] = 0, shift="I", day: Optional[date] = None, flag="OK", loom=None, style=None, beam=None):
        r = m.WvLoomReading(loom_id=(loom or self.loom).id, reading_start=start, reading_end=start + timedelta(hours=1), duration_seconds=3600, shift_id=self.shift[shift].id,
                            shift_date=day or start.date(), style_id=(style or self.style).id, beam_id=beam.id if beam else None, running_seconds=running_s, picks=picks, quality_flag=flag, data_origin="LIVE")
        self.db.add(r)
        return r

    def stop(self, start: datetime, end: Optional[datetime], reason="WARP_BREAK", shift="I", day: Optional[date] = None, loom=None, beam=None):
        e = m.WvStopEvent(loom_id=(loom or self.loom).id, started_at=start, ended_at=end, reason_id=self.reason[reason].id, shift_id=self.shift[shift].id,
                          shift_date=day or start.date(), style_id=self.style.id, beam_id=beam.id if beam else None, data_origin="LIVE")
        self.db.add(e)
        return e

    def roll(self, roll_no: str, length: float, grade: str, defects, day: date, shift="I", loom=None):
        """defects: list of (type_code, points) each counted once."""
        i = m.WvInspection(roll_no=roll_no, loom_id=(loom or self.loom).id, style_id=self.style.id, shift_id=self.shift[shift].id, shift_date=day,
                           inspected_at=datetime(day.year, day.month, day.day, 12, tzinfo=UTC), length_m=length, grade=grade, data_origin="LIVE")
        self.db.add(i)
        self.db.flush()
        for code, pts in defects:
            self.db.add(m.WvDefectObservation(inspection_id=i.id, defect_type_id=self.dtype[code].id, severity="MINOR" if pts == 1 else "MAJOR", points=pts, defect_count=1))
        return i

"""
Mill calendar: production days, shifts (including the overnight one) and reporting windows.

A *production day* starts when the first shift starts (06:00 mill time) and lasts 24 hours.
Shift III, 22:00 to 06:00, belongs to the production day it STARTED in, so a night shift is never
split across two days. All instants are timezone-aware; the database stores UTC and the mill's
local zone (settings.MILL_TIMEZONE) decides where days begin and end.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo

PERIODS = ("TODAY", "YESTERDAY", "LAST_7_DAYS", "THIS_MONTH")
PERIOD_LABELS = {"TODAY": "Today", "YESTERDAY": "Yesterday", "LAST_7_DAYS": "Last 7 days", "THIS_MONTH": "This month"}


@dataclass(frozen=True)
class ShiftDef:
    id: int
    code: str
    name: str
    start: time  # mill-local
    end: time
    sort_order: int = 0


DEFAULT_SHIFTS = (
    ShiftDef(1, "I", "Shift I", time(6, 0), time(14, 0), 1),
    ShiftDef(2, "II", "Shift II", time(14, 0), time(22, 0), 2),
    ShiftDef(3, "III", "Shift III", time(22, 0), time(6, 0), 3),
)


@dataclass(frozen=True)
class ReportWindow:
    """A reporting period, in production days, plus the exact instants it covers."""

    period: str
    label: str
    start_date: date  # first production day (inclusive)
    end_date: date  # last production day (inclusive)
    start_at: datetime  # UTC instant the first day begins
    end_at: datetime  # UTC instant the window ends: end of the last day, or `now` if that day is still running
    complete: bool  # False when the last day is still in progress

    @property
    def days(self) -> int:
        return (self.end_date - self.start_date).days + 1

    @property
    def elapsed_hours(self) -> float:
        return (self.end_at - self.start_at).total_seconds() / 3600.0


class MillCalendar:
    def __init__(self, tz: str | ZoneInfo, shifts: Sequence[ShiftDef] = DEFAULT_SHIFTS):
        self.tz = tz if isinstance(tz, ZoneInfo) else ZoneInfo(tz)
        self.shifts: List[ShiftDef] = sorted(shifts, key=lambda s: s.sort_order)
        if not self.shifts:
            raise ValueError("At least one shift is required")
        self.day_start: time = self.shifts[0].start
        self._by_id: Dict[int, ShiftDef] = {s.id: s for s in self.shifts}

    # ------------------------------------------------------------------ instants

    def _local(self, d: date, t: time) -> datetime:
        return datetime.combine(d, t, tzinfo=self.tz)

    def production_day(self, at: datetime) -> date:
        local = at.astimezone(self.tz)
        return local.date() if local.time() >= self.day_start else local.date() - timedelta(days=1)

    def day_bounds(self, d: date) -> Tuple[datetime, datetime]:
        """[start, end) of a production day, in UTC. Built from calendar dates so a DST change cannot skew it."""
        start = self._local(d, self.day_start)
        end = self._local(d + timedelta(days=1), self.day_start)
        return start.astimezone(timezone.utc), end.astimezone(timezone.utc)

    def shift_bounds(self, d: date, shift: ShiftDef) -> Tuple[datetime, datetime]:
        """[start, end) of a shift that belongs to production day `d`, in UTC."""
        start_date = d + timedelta(days=1) if shift.start < self.day_start else d
        start = self._local(start_date, shift.start)
        end_date = start_date + timedelta(days=1) if shift.end <= shift.start else start_date
        end = self._local(end_date, shift.end)
        return start.astimezone(timezone.utc), end.astimezone(timezone.utc)

    def shift_at(self, at: datetime) -> Tuple[date, ShiftDef]:
        """The production day and shift an instant falls in."""
        day = self.production_day(at)
        for s in self.shifts:
            lo, hi = self.shift_bounds(day, s)
            if lo <= at < hi:
                return day, s
        raise ValueError(f"Shifts do not cover {at.isoformat()}")  # only if the shift table has a gap

    def shift(self, shift_id: int) -> ShiftDef:
        return self._by_id[shift_id]

    # ------------------------------------------------------------------ reporting windows

    def window(self, period: str, now: Optional[datetime] = None) -> ReportWindow:
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        period = period if period in PERIODS else "TODAY"
        today = self.production_day(now)
        if period == "YESTERDAY":
            start = end = today - timedelta(days=1)
        elif period == "LAST_7_DAYS":
            start, end = today - timedelta(days=6), today
        elif period == "THIS_MONTH":
            start, end = today.replace(day=1), today
        else:
            start = end = today
        return self.window_for_dates(start, end, now, period)

    def window_for_dates(self, start: date, end: date, now: Optional[datetime] = None, period: str = "CUSTOM") -> ReportWindow:
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        start_at = self.day_bounds(start)[0]
        day_end = self.day_bounds(end)[1]
        return ReportWindow(
            period=period, label=PERIOD_LABELS.get(period, f"{start} to {end}"), start_date=start, end_date=end,
            start_at=start_at, end_at=min(day_end, now), complete=day_end <= now,
        )

    def previous(self, w: ReportWindow, now: Optional[datetime] = None) -> ReportWindow:
        """The window of equal length (in days) immediately before `w`, used as the comparison baseline."""
        n = w.days
        return self.window_for_dates(w.start_date - timedelta(days=n), w.start_date - timedelta(days=1), now, w.period)

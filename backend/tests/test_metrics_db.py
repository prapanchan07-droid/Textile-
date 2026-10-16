"""Metric formulas against the database, on small fixtures whose answers are worked out by hand."""
from datetime import date, datetime, timedelta, timezone

import pytest

from app.weaving.analytics import breakdowns, calc
from app.weaving.analytics.context import AnalysisContext
from app.core.roles import Role
from app.weaving.pages import ops, overview
from app.weaving.pages.shared import Mill
from tests.factories import FIXED_NOW, UTC, World

pytestmark = pytest.mark.pg

# Production day 2026-10-14 in mill time runs 2026-10-14 00:30 UTC to 2026-10-15 00:30 UTC.
DAY = date(2026, 10, 14)
D0 = datetime(2026, 10, 14, 0, 30, tzinfo=UTC)


def build_day(db):
    w = World(db, rpm=800, ppi=50, target_eff=90)
    # 8 normal hours: 3300 s running, 43,000 picks. One hour with a dead pick counter. One 'partial' reading.
    for h in range(8):
        w.reading(D0 + timedelta(hours=h), running_s=3300, picks=43_000)
    w.reading(D0 + timedelta(hours=8), running_s=3600, picks=None, flag="NO_PICKS")
    # Stops: two ordinary (5 and 3 min), a planned 40-minute beam change, one that began before the day and runs 10 min into it,
    # and one overnight stop (05:20 IST on the 15th, still Shift III of day 14) that is STILL OPEN.
    w.stop(D0 + timedelta(hours=1), D0 + timedelta(hours=1, minutes=5), "WARP_BREAK")
    w.stop(D0 + timedelta(hours=2), D0 + timedelta(hours=2, minutes=3), "WEFT_BREAK")
    w.stop(D0 + timedelta(hours=3), D0 + timedelta(hours=3, minutes=40), "BEAM_CHANGE")
    w.stop(D0 - timedelta(minutes=20), D0 + timedelta(minutes=10), "MECHANICAL", shift="III", day=date(2026, 10, 13))
    w.stop(datetime(2026, 10, 14, 23, 50, tzinfo=UTC), None, "ELECTRICAL", shift="III", day=DAY)
    db.flush()
    return w


def ctx(db, period="YESTERDAY"):
    return AnalysisContext(db, now=FIXED_NOW, period=period)


def test_production_formulas_with_missing_counter(db):
    build_day(db)
    c = ctx(db)
    a = calc.total_production(c.prod_between(c.window.start_date, c.window.end_date))
    assert a.readings == 9 and a.no_picks == 1
    assert a.scheduled_s == 9 * 3600
    assert a.running_s == 8 * 3300 + 3600
    assert a.utilization_pct == pytest.approx(30000 / 32400 * 100)
    # the reading with no counter is excluded from BOTH sides of efficiency
    assert a.picks == 8 * 43_000 and a.capacity_picks == pytest.approx(800 * 480)
    assert a.efficiency_pct == pytest.approx(344_000 / 384_000 * 100)
    ppm = 50 * 39.3701
    assert a.meters == pytest.approx(344_000 / ppm)
    assert a.target_meters == pytest.approx(0.9 * 384_000 / ppm)
    assert a.achievement_pct == pytest.approx(344_000 / (0.9 * 384_000) * 100)


def test_stoppage_formulas_overnight_open_and_planned(db):
    build_day(db)
    c = ctx(db)
    s = calc.total_stops(c.stops_window)
    prod = calc.total_production(c.prod_between(c.window.start_date, c.window.end_date))
    # events that STARTED in the window: warp, weft, beam change, overnight electrical (the one that began before the window is not counted)
    assert s.events == 4
    # eligible for the stop rate: warp, weft, electrical (planned beam change excluded)
    assert s.eligible_events == 3
    assert s.per_100k_picks(prod.picks) == pytest.approx(3 / 344_000 * 100_000)
    # downtime clipped to the window: 5 + 3 + 40 + 10 (clipped from 30) + 40 (open stop, clipped at the window end 00:30)
    assert s.downtime_min == pytest.approx(98)
    assert s.unplanned_downtime_min == pytest.approx(58)
    # open stops are counted separately and are not in the average duration; planned stops are not either
    assert s.open_events == 1
    assert s.closed_events == 2 and s.avg_duration_min == pytest.approx((5 + 3) / 2)


def test_open_stop_counts_up_to_now_in_a_live_window(db):
    w = World(db)
    start = FIXED_NOW - timedelta(minutes=45)
    w.reading(FIXED_NOW - timedelta(hours=2), picks=1000)
    w.stop(start, None, "MECHANICAL", shift="II", day=date(2026, 10, 15))
    db.flush()
    c = ctx(db, "TODAY")
    s = calc.total_stops(c.stops_window)
    assert s.downtime_min == pytest.approx(45) and s.open_events == 1
    mill = Mill(db, Role.WEAVING_MANAGER, "TODAY", now=FIXED_NOW)
    live = overview.command(mill)["live"]
    assert live["stopped"] == 1 and live["stopped_now"][0]["loom"] == "T-01" and live["stopped_now"][0]["minutes"] == 45


def test_overnight_stop_is_attributed_to_the_shift_and_day_it_started(db):
    w = build_day(db)
    c = ctx(db)
    by_shift = calc.roll_stops(c.stops_window, lambda r: c.refs.shift_name(r.shift_id))
    assert by_shift["Shift III"].events == 1 and by_shift["Shift III"].open_events == 1
    rows = breakdowns.stoppage_breakdown(c, "shift")
    assert any(r["key"] == "Shift III" for r in rows)


def test_quality_formulas(db):
    w = World(db)
    w.roll("R1", 100, "A", [("FLOAT", 1), ("SLUB", 1)], DAY)
    w.roll("R2", 100, "B", [("FLOAT", 3)] * 6, DAY)
    w.roll("R3", 50, "C", [("HOLE", 4)] * 5, DAY)
    db.flush()
    c = ctx(db)
    insp, defs = c.insp_between(DAY, DAY)
    q = calc.total_quality(insp, defs)
    assert q.length_m == 250 and q.defects == 13
    assert q.defects_per_100m == pytest.approx(13 / 250 * 100)
    assert q.points == 2 + 18 + 20 and q.points_per_100m == pytest.approx(40 / 250 * 100)
    assert q.grade_a_pct == pytest.approx(40) and q.grade_b_pct == pytest.approx(40) and q.grade_c_pct == pytest.approx(20)


def test_quality_breakdown_reports_inspection_coverage(db):
    w = build_day(db)
    w.roll("R1", 87.4, "A", [], DAY)
    db.flush()
    rows = breakdowns.quality_breakdown(ctx(db), "style")
    assert rows[0]["inspected_m"] == 87 and rows[0]["inspection_coverage_pct"] is not None and rows[0]["inspection_coverage_pct"] < 100


def test_empty_database_gives_honest_empty_pages(db):
    """A fresh deployment has no looms at all: every page must still render, with empty lists and no invented numbers."""
    mill = Mill(db, Role.WEAVING_MANAGER, "LAST_7_DAYS", now=FIXED_NOW)
    prod = ops.production(mill)
    assert prod["looms"] == [] and prod["trend"] == [] and prod["forecast"] is None
    assert all(k["value"] in (None, 0, 0.0) for k in prod["kpis"] if k["label"] in ("Output", "Efficiency"))
    cmd = overview.command(Mill(db, Role.WEAVING_MANAGER, "TODAY", now=FIXED_NOW))
    assert cmd["live"]["total"] == 0 and cmd["live"]["stopped_now"] == []


def test_window_without_readings_has_no_efficiency_not_zero(db):
    World(db)
    prod = ops.production(Mill(db, Role.WEAVING_MANAGER, "YESTERDAY", now=FIXED_NOW))
    eff = next(k for k in prod["kpis"] if k["label"] == "Efficiency")
    assert eff["value"] is None


def test_group_by_rejects_nothing_silently_on_empty_data(db):
    World(db)
    c = ctx(db)
    assert breakdowns.production_breakdown(c, "loom") == []
    assert breakdowns.stoppage_breakdown(c, "cause") == []
    assert breakdowns.quality_breakdown(c, "defect_type") == []


def test_no_findings_on_an_empty_database(db):
    from app.weaving.analytics import investigations as inv

    c = AnalysisContext(db, now=FIXED_NOW, period="LAST_7_DAYS")
    assert inv.all_findings(c, include_maintenance=True) == []

"""Pure-logic tests: mill calendar (overnight shifts, windows), statistics, and metric formulas. No database."""
import math
from datetime import date, datetime, time, timedelta, timezone

import pytest

from app.weaving.analytics import calc, stats
from app.weaving.analytics.calendar import MillCalendar
from app.weaving.analytics.facts import ProdRow, StopRow

UTC = timezone.utc
cal = MillCalendar("Asia/Kolkata")


def ist(y, mo, d, h, mi=0):
    return datetime(y, mo, d, h, mi, tzinfo=cal.tz).astimezone(UTC)


# ------------------------------------------------------------------ calendar

def test_production_day_starts_at_first_shift():
    assert cal.production_day(ist(2026, 10, 15, 6, 0)) == date(2026, 10, 15)
    assert cal.production_day(ist(2026, 10, 15, 5, 59)) == date(2026, 10, 14)
    assert cal.production_day(ist(2026, 10, 15, 23, 59)) == date(2026, 10, 15)


def test_night_shift_belongs_to_the_day_it_started_in():
    # 02:00 on the 16th is still Shift III of production day the 15th
    day, shift = cal.shift_at(ist(2026, 10, 16, 2, 0))
    assert (day, shift.code) == (date(2026, 10, 15), "III")
    day, shift = cal.shift_at(ist(2026, 10, 15, 22, 0))
    assert (day, shift.code) == (date(2026, 10, 15), "III")
    day, shift = cal.shift_at(ist(2026, 10, 16, 6, 0))
    assert (day, shift.code) == (date(2026, 10, 16), "I")


def test_shift_bounds_overnight_cross_midnight_and_tile_the_day():
    s3 = cal.shifts[2]
    start, end = cal.shift_bounds(date(2026, 10, 15), s3)
    assert start == ist(2026, 10, 15, 22) and end == ist(2026, 10, 16, 6)
    # the three shifts exactly tile the production day, with no gap or overlap
    bounds = sorted(cal.shift_bounds(date(2026, 10, 15), s) for s in cal.shifts)
    assert bounds[0][0] == cal.day_bounds(date(2026, 10, 15))[0] and bounds[-1][1] == cal.day_bounds(date(2026, 10, 15))[1]
    assert all(a[1] == b[0] for a, b in zip(bounds, bounds[1:]))


def test_every_hour_of_a_week_maps_to_exactly_one_shift():
    t = ist(2026, 10, 10, 0)
    for _ in range(24 * 7):
        day, shift = cal.shift_at(t)
        lo, hi = cal.shift_bounds(day, shift)
        assert lo <= t < hi
        t += timedelta(hours=1)


def test_today_at_3am_is_still_yesterdays_production_day():
    w = cal.window("TODAY", ist(2026, 10, 15, 3, 0))
    assert w.start_date == w.end_date == date(2026, 10, 14)
    assert not w.complete  # shift III is still running


def test_windows_and_previous_window():
    now = ist(2026, 10, 15, 12)
    w7 = cal.window("LAST_7_DAYS", now)
    assert (w7.start_date, w7.end_date, w7.days) == (date(2026, 10, 9), date(2026, 10, 15), 7)
    p = cal.previous(w7, now)
    assert (p.start_date, p.end_date) == (date(2026, 10, 2), date(2026, 10, 8)) and p.complete
    y = cal.window("YESTERDAY", now)
    assert y.complete and y.end_at == cal.day_bounds(date(2026, 10, 14))[1]
    mtd = cal.window("THIS_MONTH", now)
    assert (mtd.start_date, mtd.days) == (date(2026, 10, 1), 15)
    assert cal.window("nonsense", now).period == "TODAY"


# ------------------------------------------------------------------ statistics

def test_binomial_tail_known_values():
    assert stats.binomial_sf(0, 10, 0.5) == 1.0
    assert stats.binomial_sf(10, 10, 0.5) == pytest.approx(1 / 1024)
    assert stats.binomial_sf(6, 10, 0.5) == pytest.approx(386 / 1024)
    assert stats.binomial_sf(11, 10, 0.5) == 0.0


def test_rate_ratio_test_detects_a_real_difference_and_not_noise():
    ratio, p = stats.rate_ratio_test(60, 1000, 20, 1000)
    assert ratio == pytest.approx(3.0) and p < 1e-5
    ratio, p = stats.rate_ratio_test(21, 1000, 20, 1000)
    assert p > 0.3
    assert stats.rate_ratio_test(5, 0, 5, 10) == (None, None)  # no exposure: no answer, not zero


def test_level_shift_finds_the_step():
    series = [90, 91, 89, 90, 90, 91, 90, 82, 81, 83, 82, 81]
    r = stats.level_shift(series)
    assert r["index"] == 7 and r["before_mean"] > 89 and r["after_mean"] < 83 and r["p_lower"] < 0.001
    assert stats.level_shift([90, 91, 90]) is None  # too short to say


def test_level_shift_on_flat_noise_is_not_significant():
    r = stats.level_shift([90.0, 90.4, 89.8, 90.1, 90.2, 89.9, 90.3, 90.0])
    assert r["before_mean"] - r["after_mean"] < 1.0


# ------------------------------------------------------------------ formulas

def prod_row(**kw):
    base = dict(loom_id=1, shift_date=date(2026, 10, 14), shift_id=1, style_id=1, beam_id=None, weaver_id=None, scheduled_s=0, running_s=0, measured_s=0, measured_running_s=0,
                picks=0, capacity_picks=0, meters=0, target_meters=0, readings=0, no_picks=0, partial=0, demo=0)
    base.update(kw)
    return ProdRow(**base)


def stop_row(**kw):
    base = dict(loom_id=1, reason_id=1, shift_id=1, shift_date=date(2026, 10, 14), style_id=1, beam_id=None, weaver_id=None, is_planned=False, counts_toward_rate=True,
                events=0, eligible_events=0, downtime_s=0, closed_events=0, closed_duration_s=0, open_events=0, demo=0)
    base.update(kw)
    return StopRow(**base)


def test_prod_formulas():
    a = calc.total_production([prod_row(scheduled_s=36000, running_s=33000, measured_s=32400, measured_running_s=29700, picks=1_000_000, capacity_picks=1_080_000, meters=500, target_meters=540)])
    assert a.utilization_pct == pytest.approx(33000 / 36000 * 100)
    assert a.efficiency_pct == pytest.approx(1_000_000 / 1_080_000 * 100)
    assert a.achievement_pct == pytest.approx(500 / 540 * 100)
    assert a.run_rate_m_per_min == pytest.approx(500 / (29700 / 60))


def test_undefined_metrics_are_none_not_zero():
    a = calc.ProdAgg()
    assert a.utilization_pct is None and a.efficiency_pct is None and a.achievement_pct is None and a.run_rate_m_per_min is None
    s = calc.StopAgg()
    assert s.avg_duration_min is None and s.per_100k_picks(0) is None
    q = calc.QualAgg()
    assert q.defects_per_100m is None and q.grade_a_pct is None


def test_stop_formulas():
    s = calc.total_stops([stop_row(events=10, eligible_events=8, downtime_s=1800, closed_events=6, closed_duration_s=900, open_events=1),
                          stop_row(events=2, eligible_events=0, downtime_s=2400, is_planned=True)])
    assert s.eligible_events == 8 and s.per_100k_picks(400_000) == pytest.approx(2.0)
    assert s.avg_duration_min == pytest.approx(900 / 6 / 60)
    assert s.downtime_min == pytest.approx(70) and s.unplanned_downtime_min == pytest.approx(30)


def test_downtime_impact_uses_running_output_and_contribution():
    params = {1: calc.LoomImpactParams(run_rate_m_per_min=2.0, contribution_per_m=40.0, basis="observed")}
    imp = calc.downtime_impact([stop_row(downtime_s=600), stop_row(downtime_s=1200, is_planned=True)], params)
    assert imp.lost_m == pytest.approx(20.0)  # 10 min x 2 m/min; the planned stop is left out
    assert imp.lost_lakhs == pytest.approx(20 * 40 / 100000)
    assert calc.downtime_impact([stop_row(downtime_s=1200, is_planned=True)], params, include_planned=True).lost_m == pytest.approx(40.0)
    assert calc.downtime_impact([stop_row(loom_id=99, downtime_s=600)], params).lost_m == 0.0  # unknown loom: no invented number

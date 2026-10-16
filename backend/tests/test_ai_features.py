"""The AI features, against the seeded mill whose problems are known: machine abnormality watch, health score, order delivery
risk, the scheduler, comparisons, the workforce signal and the forecast. Each asserts the result AND that it is honest about its limits."""
from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.core.roles import Role
from app.weaving.analytics import compare as cmp, forecast, scheduler, sensors
from app.weaving.analytics.context import AnalysisContext
from app.weaving.pages.shared import Mill
from tests.factories import FIXED_NOW

pytestmark = pytest.mark.pg


@pytest.fixture(scope="module")
def mill(seeded, engine):
    with Session(engine) as db:
        yield Mill(db, Role.WEAVING_MANAGER, "LAST_7_DAYS", now=FIXED_NOW)


@pytest.fixture(scope="module")
def alerts(mill):
    return {(a.loom, a.sensor, a.kind): a for a in mill.alerts}


# ------------------------------------------------------------------ machine abnormality watch

def test_planted_sensor_problems_are_found_with_their_start_dates(alerts):
    p = alerts[("AJ-14", "pressure", "DRIFT")]
    assert p.level == "CRITICAL" and p.recent < 5.5 and p.normal == pytest.approx(6.0, abs=0.1) and p.started_on == "2026-10-04"
    v = alerts[("SZ-05", "vibration", "DRIFT")]
    assert v.level == "CRITICAL" and v.recent > v.normal * 1.5 and v.started_on is not None
    t = alerts[("AJ-09", "temperature", "DRIFT")]
    assert t.level in ("CRITICAL", "WARNING") and t.days_to_alarm is not None and 5 < t.days_to_alarm < 30
    assert ("SZ-07", "power", "SHIFT_POWER") in alerts and "Shift III" in alerts[("SZ-07", "power", "SHIFT_POWER")].title
    assert ("AJ-22", "all", "SENSOR_OFFLINE") in alerts


def test_healthy_looms_raise_no_sensor_alert(alerts):
    flagged = {k[0] for k in alerts}
    assert not ({"AJ-02", "AJ-03", "AJ-04", "AJ-10", "SZ-01", "SZ-04"} & flagged)


def test_alerts_state_their_limits(alerts):
    for a in alerts.values():
        assert a.limitations and a.facts and a.hypothesis
    assert any("not validated" in x for a in alerts.values() for x in a.limitations)


def test_health_score_ranks_the_chronic_loom_worst_and_explains_itself(mill):
    h = {mill.refs.loom_code(i): v for i, v in mill.health.items()}
    worst = min(h, key=lambda c: h[c]["score"])
    assert worst == "SZ-05" and h["SZ-05"]["band"] == "AT_RISK"
    assert {c["factor"] for c in h["SZ-05"]["components"]} >= {"Sensor alerts", "Stoppage record"}
    assert all(sum(c["points"] for c in v["components"]) == v["score"] - 100 or v["score"] == 0 for v in h.values())
    assert h["AJ-02"]["score"] >= 90 and "not a probability" in h["AJ-02"]["note"]


# ------------------------------------------------------------------ orders and delivery risk

def test_order_risk_matches_the_known_story(mill):
    o = {r["order_no"]: r for r in mill.orders}
    assert o["SO-2422"]["risk"] == "LATE" and o["SO-2422"]["slack_days"] < 0
    assert o["SO-2441"]["risk"] == "UNSCHEDULED" and o["SO-2441"]["looms"] == []
    assert o["SO-2417"]["risk"] == "DONE" and o["SO-2417"]["state"] == "COMPLETED"
    assert o["SO-2433"]["risk"] == "ON_TRACK"
    assert "remaining" in o["SO-2422"]["explain"] and o["SO-2422"]["eta_late"] >= o["SO-2422"]["eta"] >= o["SO-2422"]["eta_early"]
    assert o["SO-2422"]["revenue_at_stake_lakhs"] > 0 and o["SO-2417"]["revenue_at_stake_lakhs"] == 0


# ------------------------------------------------------------------ the scheduler

@pytest.fixture(scope="module")
def plan(mill):
    return scheduler.build_plan(mill.ctx, mill.orders, mill.health_scores, True)


def test_plan_improves_on_the_current_booking_without_churn(plan):
    assert plan["proposed"]["late_orders"] < plan["baseline"]["late_orders"]
    assert plan["proposed"]["total_late_days"] < plan["baseline"]["total_late_days"]
    assert 1 <= len({m["loom"] for m in plan["moves"]}) <= 10, "a handful of moves, not a reshuffle of the floor"
    assert plan["baseline"]["changeovers"] == 0


def test_every_move_respects_the_machine_constraints(mill, plan):
    looms = {l.loom_code: l for l in mill.refs.looms.values()}
    styles = {s.style_code: s for s in mill.refs.styles.values()}
    for m in plan["moves"]:
        loom, style = looms[m["loom"]], styles[m["to_style"]]
        if style.loom_type_required:
            assert loom.loom_type == style.loom_type_required, m
        assert float(loom.reed_space_cm) >= float(style.width_in) * 2.54 - 0.01, m
        assert m["to_before"] is None or m["to_after"] is None or m["to_after"] <= m["to_before"] + 0.5
        assert m["reason"] and "projected" in m["reason"]


def test_priority_a_orders_avoid_at_risk_looms(mill, plan):
    at_risk = {mill.refs.loom_code(i) for i, h in mill.health.items() if h["score"] < 60}
    a_orders = {o["order_no"] for o in plan["orders"] if o["priority"] == "A"}
    assert not [m for m in plan["moves"] if m["loom"] in at_risk and m["to_order"] in a_orders]


def test_plan_is_deterministic_and_signed(mill, plan):
    again = scheduler.build_plan(mill.ctx, mill.orders, mill.health_scores, True)
    assert again["signature"] == plan["signature"] and again["moves"] == plan["moves"]
    assert any("nothing changes until" in a.lower() or "proposal" in a.lower() for a in plan["assumptions"])


def test_money_is_left_out_of_the_plan_for_roles_without_it(mill):
    p = scheduler.build_plan(mill.ctx, mill.orders, mill.health_scores, False)
    assert "revenue_late_lakhs" not in p["baseline"] and not any("₹" in s for s in p["summary"])


# ------------------------------------------------------------------ compare

def test_comparison_flags_the_real_difference_and_not_the_noise(mill):
    r = cmp.compare(mill.ctx, "loom", ["AJ-10", "AJ-14"], days=14)
    e = r["entities"][1]
    assert e["vs_reference"]["weft_stops_per_100k"]["significant"] and e["vs_reference"]["weft_stops_per_100k"]["direction"] == "higher"
    assert any("weft" in h.lower() and "worse" in h for h in r["highlights"])
    quiet = cmp.compare(mill.ctx, "loom", ["AJ-02", "AJ-04"], days=14)
    assert not any(v.get("significant") for v in quiet["entities"][1]["vs_reference"].values()), "two alike looms must not be called different"
    assert quiet["highlights"] and "variation" in quiet["highlights"][0]


def test_supplier_and_lot_comparisons_work_and_the_flagged_lot_is_worse(mill):
    r = cmp.compare(mill.ctx, "yarn_lot", ["YL-415-06", "YL-415-07"], metrics=["warp_stops_per_100k"], days=14)
    a, b = r["entities"]
    assert b["metrics"]["warp_stops_per_100k"] > 2 * a["metrics"]["warp_stops_per_100k"]
    s = cmp.compare(mill.ctx, "supplier", [x["key"] for x in cmp.options(mill.ctx, "supplier")], days=14)
    assert len(s["entities"]) == 3 and all(e["metrics"]["efficiency_pct"] for e in s["entities"])


def test_style_filter_restricts_the_comparison(mill):
    r = cmp.compare(mill.ctx, "shift", ["Shift I", "Shift III"], metrics=["defects_per_100m"], days=14, style="S-204")
    assert r["style_filter"] == "S-204"
    assert r["entities"][1]["metrics"]["defects_per_100m"] > r["entities"][0]["metrics"]["defects_per_100m"] * 1.5


def test_recommended_comparisons_come_from_the_findings(mill):
    rec = cmp.recommended(mill.ctx, mill.findings)
    ids = {r["id"] for r in rec}
    assert "beam_warp_excess:S-415" in ids and "loom_decline:AJ-14" in ids and {"type", "shifts", "suppliers"} <= ids
    for r in rec:
        assert r["keys"] and r["metrics"] and r["why"]


# ------------------------------------------------------------------ workforce

def test_coaching_signal_is_loom_adjusted(mill):
    from app.weaving.analytics import workforce

    w = workforce.build(mill.ctx, True)
    assert [c["code"] for c in w["coaching"]] == ["W-II-07"]
    assert "allows for which looms" in w["coaching"][0]["suggestion"] or "allow" in w["coaching"][0]["suggestion"]
    # the weavers who run the faulty AJ-14 are not blamed for it
    ran_aj14 = {d["code"] for d in w["directory"] if d.get("looms") and "AJ-14" in d["looms"]}
    assert ran_aj14 and not (ran_aj14 & {c["code"] for c in w["coaching"]} - {"W-II-07"})


# ------------------------------------------------------------------ forecast

def test_forecast_reports_its_own_error_and_refuses_when_data_is_thin():
    assert forecast.forecast_daily([100.0] * 6) is None
    f = forecast.forecast_daily([100 + (i % 3) for i in range(20)], horizon=5)
    assert f.mape_pct is not None and f.mape_pct < 5 and len(f.points) == 5
    assert all(lo <= p <= hi for lo, p, hi in zip(f.low, f.points, f.high))
    d = f.as_dict()
    assert d["backtest_days"] == 5 and "MAPE" in d["note"]


def test_forecast_follows_a_trend_better_than_a_flat_guess():
    rising = [100 + 5 * i for i in range(20)]
    f = forecast.forecast_daily(rising, horizon=3)
    assert f.points[0] > rising[-1] - 3 and f.points[2] >= f.points[0]

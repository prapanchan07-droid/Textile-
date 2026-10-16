"""Root-cause foundations: the planted situations are found, with evidence, and nothing is claimed as a verified cause."""
import pytest

from app.weaving.analytics import investigations as inv
from app.weaving.analytics.context import AnalysisContext
from tests.factories import FIXED_NOW

pytestmark = pytest.mark.pg


@pytest.fixture(scope="module")
def findings(seeded, engine):
    from sqlalchemy.orm import Session

    with Session(engine) as db:
        ctx = AnalysisContext(db, now=FIXED_NOW, period="LAST_7_DAYS")
        yield {f.key: f for f in inv.all_findings(ctx, include_maintenance=True)}, ctx, db


def test_loom_decline_found_with_the_right_start_date(findings):
    f = findings[0]["loom_decline:AJ-14"]
    # the seed starts AJ-14's decline on demo day 9; the epoch is 21 days before the end
    assert f.evidence.observed["decline_started_on"] == "2026-10-04"
    assert f.evidence.baseline["efficiency_before_pct"] - f.evidence.observed["efficiency_after_pct"] > 5
    assert any("Weft break stops rose" in x for x in f.facts), f.facts
    assert f.signals and f.signals[0].p_value < 1e-6


def test_recurring_patterns_found_including_shift_concentration(findings):
    f = findings[0]["recurring_stop:SZ-05:MECHANICAL"]
    assert f.evidence.observed["days_with_stops"] >= 3 and f.evidence.estimated_impact.lost_m > 0
    g = findings[0]["recurring_stop:SZ-07:ELECTRICAL"]
    assert any("Shift III" in x for x in g.facts), g.facts
    assert any(s.name.startswith("Stops concentrated") for s in g.signals)


def test_beam_and_yarn_lot_finding_lists_hypotheses_but_no_cause(findings):
    f = findings[0]["beam_warp_excess:S-415"]
    assert f.evidence.scope["yarn_lots"] == "YL-415-07"
    assert f.evidence.baseline["other_beams_per_100k_picks"] < f.evidence.observed["per_100k_picks"]
    assert any("lot" in h.statement.lower() for h in f.hypotheses)


def test_shift_quality_finding(findings):
    f = findings[0]["shift_defect_shift:III:S-204"]
    assert f.evidence.scope == {"style": "S-204", "shift": "Shift III"}
    assert f.evidence.observed["defects_per_100m"] > f.evidence.baseline["other_shifts_defects_per_100m"] * 1.4
    assert any("Float" in x or "Warp streak" in x for x in f.facts)


def test_every_finding_carries_complete_evidence_and_no_verified_cause(findings):
    for f in findings[0].values():
        assert f.evidence.period and f.evidence.scope and f.evidence.observed is not None and f.evidence.n_observations > 0
        assert f.confidence.level in {"HIGH", "MEDIUM", "LOW"} and f.confidence.reasons
        assert f.evidence.limitations, f.key  # data limitations are always stated
        assert f.verified_cause is None
        assert all(h.status == "UNVERIFIED" and h.how_to_check for h in f.hypotheses)
        assert f.requires_human_approval is True
        assert f.audiences, f.key
        assert f.next_steps, f.key


def test_healthy_looms_are_not_flagged(findings):
    flagged = {k.split(":")[1] for k in findings[0] if k.startswith(("loom_decline", "recurring_stop"))}
    # AJ-02 .. AJ-04 run normally in the seed
    assert not ({"AJ-02", "AJ-03", "AJ-04"} & flagged)


def test_findings_are_ranked_and_focus_list_is_per_role(findings):
    allf = list(findings[0].values())
    scores = [f.priority_score for f in inv.sort_findings(allf)]
    assert scores == sorted(scores, reverse=True)
    quality = inv.priorities_for("QUALITY", allf, 10)
    assert quality and all("QUALITY" in f.audiences for f in quality)
    assert {f.kind for f in quality} <= {"beam_warp_excess", "shift_defect_shift"}
    maint = inv.priorities_for("MAINTENANCE", allf, 10)
    assert all("MAINTENANCE" in f.audiences for f in maint)


def test_maintenance_ranking_puts_the_chronic_loom_first(findings):
    ranked = [f for f in findings[0].values() if f.kind == "maintenance_priority"]
    ranked.sort(key=lambda f: -f.priority_score)
    assert ranked[0].evidence.scope["loom"] == "SZ-05"


def test_beam_change_effect_reports_pairs_without_claiming_cause(findings):
    _, ctx, _ = findings
    r = inv.beam_change_effect(ctx, "S-415")
    assert r["pairs"] and "Association only" in r["note"]
    assert r["pooled"]["beam_changes"] == len(r["pairs"])
    assert inv.beam_change_effect(ctx, "NOPE")["pairs"] == []

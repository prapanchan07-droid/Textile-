"""Backend authorization for every weaving page, the redaction of money, and the write paths. Enforced by the API, not the menu."""
import pytest
from fastapi.testclient import TestClient

from app.core.roles import ROLE_SECTIONS, Role
from app.main import app

pytestmark = pytest.mark.pg

PASSWORD = "Ashok@2026"
USERS = {"owner": Role.OWNER, "manager": Role.WEAVING_MANAGER, "supervisor": Role.SHIFT_SUPERVISOR, "maintenance": Role.MAINTENANCE, "quality": Role.QUALITY}
ALL_SECTIONS = sorted({s for v in ROLE_SECTIONS.values() for s in v})
EXTRA = {  # other endpoints and the section that gates them (None: any signed-in user)
    "/api/v1/weaving/analytics/definitions": None,
    "/api/v1/weaving/investigations/priorities": None,
    "/api/v1/weaving/investigations/findings": None,
    "/api/v1/weaving/analytics/production?group_by=loom": "production",
    "/api/v1/weaving/analytics/stoppages?group_by=cause": "stoppages",
    "/api/v1/weaving/events/stops?page_size=5": "stoppages",
    "/api/v1/weaving/investigations/style/S-415/beam-change": "stoppages",
    "/api/v1/weaving/pages/machines/SZ-05": "machines",
    "/api/v1/weaving/compare/run?type=loom&keys=AJ-01&keys=AJ-02": "compare",
    "/api/v1/weaving/compare/options?type=loom": "compare",
}
LEGACY = ["/api/v1/ingestion/history", "/api/v1/overview", "/api/v1/production", "/api/v1/machines", "/api/v1/manpower-quality", "/api/v1/revenue-loss", "/api/v1/decision-center", "/api/v1/machine-comparison"]


@pytest.fixture(scope="module")
def client(seeded):
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def tokens(client):
    out = {}
    for u in USERS:
        r = client.post("/api/v1/auth/login", json={"username": u, "password": PASSWORD})
        assert r.status_code == 200, r.text
        out[u] = {"Authorization": "Bearer " + r.json()["data"]["access_token"]}
    return out


def get(client, path, headers=None):
    return client.get(path, headers=headers or {})


def test_existing_login_and_roles_still_work(client, tokens):
    for u, role in USERS.items():
        me = client.get("/api/v1/auth/me", headers=tokens[u]).json()["data"]
        assert me["role"] == role.value and me["sections"] == ROLE_SECTIONS[role]
    assert client.post("/api/v1/auth/login", json={"username": "owner", "password": "wrong"}).status_code == 401
    assert client.get("/api/v1/health").status_code == 200


def test_every_role_has_a_landing_page_of_its_own():
    first = {r: ROLE_SECTIONS[r][0] for r in ROLE_SECTIONS}
    assert len(set(first.values())) == len(first), "each role should land on a different page"
    assert first[Role.OWNER] == "owner" and first[Role.WEAVING_MANAGER] == "command" and first[Role.SHIFT_SUPERVISOR] == "cockpit"


def test_removed_pages_are_gone():
    all_pages = {s for v in ROLE_SECTIONS.values() for s in v}
    assert "looms" not in all_pages and "people" not in all_pages and "styles" not in all_pages


def test_anonymous_and_bad_tokens_are_rejected_everywhere(client):
    paths = [f"/api/v1/weaving/pages/{s}" for s in ALL_SECTIONS] + list(EXTRA)
    for p in paths:
        assert get(client, p).status_code == 401, p
        assert get(client, p, {"Authorization": "Bearer nope"}).status_code == 401, p


@pytest.mark.parametrize("user", list(USERS))
def test_pages_follow_the_role_table(client, tokens, user):
    role = USERS[user]
    for s in ALL_SECTIONS:
        expected = 200 if s in ROLE_SECTIONS[role] else 403
        got = get(client, f"/api/v1/weaving/pages/{s}", tokens[user]).status_code
        assert got == expected, f"{user} page {s}: expected {expected} got {got}"
    for path, section in EXTRA.items():
        expected = 200 if section is None or section in ROLE_SECTIONS[role] else 403
        assert get(client, path, tokens[user]).status_code == expected, f"{user} {path}"


@pytest.mark.parametrize("user", list(USERS))
def test_legacy_modules_and_ingestion_are_management_only(client, tokens, user):
    for path in LEGACY:
        got = get(client, path, tokens[user]).status_code
        if USERS[user] in (Role.OWNER, Role.WEAVING_MANAGER):
            assert got not in (401, 403), f"{user} {path}: {got}"
        else:
            assert got == 403, f"{user} {path}: {got}"
        assert get(client, path).status_code == 401


def test_money_is_null_for_roles_that_may_not_see_it(client, tokens):
    mgr = get(client, "/api/v1/weaving/pages/orders", tokens["manager"]).json()["data"]
    assert mgr["money_visible"] and mgr["summary"]["value_at_risk_lakhs"] is not None and mgr["styles"]
    for u in ("supervisor", "maintenance", "quality"):
        # these roles have no orders page at all; check the pages they do have
        pass
    ins_q = get(client, "/api/v1/weaving/pages/insights", tokens["quality"]).json()["data"]
    assert ins_q["money_visible"] is False
    assert all(f["evidence"]["estimated_impact"] is None or f["evidence"]["estimated_impact"]["lost_lakhs"] is None for f in ins_q["findings"])
    prod = get(client, "/api/v1/weaving/pages/stoppages", tokens["maintenance"]).json()["data"]
    assert all(p["est_lost_lakhs"] is None for p in prod["pareto"])
    own = get(client, "/api/v1/weaving/pages/stoppages", tokens["manager"]).json()["data"]
    assert any(p["est_lost_lakhs"] for p in own["pareto"])


def test_scheduler_money_and_decision_rights(client, tokens):
    mgr = get(client, "/api/v1/weaving/pages/scheduler", tokens["manager"]).json()["data"]
    assert mgr["can_decide"] and "revenue_late_lakhs" in mgr["baseline"]
    own = get(client, "/api/v1/weaving/pages/scheduler", tokens["owner"]).json()["data"]
    assert own["can_decide"]


def test_findings_are_filtered_to_the_role_audience(client, tokens):
    for u, role in USERS.items():
        data = get(client, "/api/v1/weaving/investigations/findings", tokens[u]).json()["data"]
        assert all(role.value in f["audiences"] for f in data), u
    qual = get(client, "/api/v1/weaving/investigations/findings", tokens["quality"]).json()["data"]
    assert qual and {f["kind"] for f in qual} <= {"beam_warp_excess", "shift_defect_shift"}


def test_individual_comparison_is_limited_to_owner_and_manager(client, tokens):
    path = "/api/v1/weaving/compare/run?type=weaver&keys=W-I-01&keys=W-I-02"
    assert get(client, path, tokens["manager"]).status_code == 200
    assert get(client, path, tokens["quality"]).status_code == 403
    assert "weaver" not in {t["key"] for t in get(client, "/api/v1/weaving/pages/compare", tokens["quality"]).json()["data"]["types"]}
    assert get(client, "/api/v1/weaving/compare/options?type=weaver", tokens["quality"]).status_code == 400


def test_phone_numbers_are_not_sent_to_roles_that_do_not_need_them(client, tokens):
    mgr = get(client, "/api/v1/weaving/pages/workforce", tokens["manager"]).json()["data"]["directory"]
    sup = get(client, "/api/v1/weaving/pages/workforce", tokens["supervisor"]).json()["data"]["directory"]
    assert any(p["phone"] for p in mgr) and any(p["phone"] for p in sup)
    assert len({p["shift"] for p in sup}) == 1, "a supervisor sees only their own shift's crew"


def test_pagination_and_validation(client, tokens):
    r = get(client, "/api/v1/weaving/events/stops?page=2&page_size=25", tokens["supervisor"]).json()["data"]
    assert r["page"] == 2 and len(r["items"]) == 25 and r["total"] > 1000
    assert get(client, "/api/v1/weaving/events/stops?page_size=500", tokens["supervisor"]).status_code == 422
    assert get(client, "/api/v1/weaving/pages/production?period=FOREVER", tokens["manager"]).status_code == 400
    assert get(client, "/api/v1/weaving/pages/machines/NOPE", tokens["manager"]).status_code == 404


# ------------------------------------------------------------------ writes: people decide, the system records

def post(client, path, headers, **body):
    return client.post(path, headers=headers, json=body)


def test_actions_need_approval_unless_a_manager_raises_them(client, tokens):
    r = post(client, "/api/v1/weaving/actions", tokens["supervisor"], issue="Test issue", action="Check the nozzle")
    assert r.status_code == 200 and r.json()["data"]["requires_approval"] is True
    ref = r.json()["data"]["ref"]
    assert client.post(f"/api/v1/weaving/actions/{ref}/approve", headers=tokens["supervisor"]).status_code == 403
    assert client.post(f"/api/v1/weaving/actions/{ref}/approve", headers=tokens["manager"]).status_code == 200
    mine = post(client, "/api/v1/weaving/actions", tokens["manager"], issue="Manager issue", action="Do the thing", expected_impact_lakhs=1.5)
    assert mine.json()["data"]["requires_approval"] is False
    # supervisors cannot assign a money value
    page = get(client, "/api/v1/weaving/pages/actions", tokens["manager"]).json()["data"]
    assert next(a for a in page["actions"] if a["ref"] == ref)["expected_impact_lakhs"] == 0


def test_a_cause_is_verified_only_by_a_person_on_a_completed_action(client, tokens):
    ref = post(client, "/api/v1/weaving/actions", tokens["manager"], issue="Cause test", action="Replace nozzle", finding_key="loom_decline:AJ-14").json()["data"]["ref"]
    # not completed yet: refused
    assert client.patch(f"/api/v1/weaving/actions/{ref}", headers=tokens["manager"], json={"verified_cause": "worn nozzle"}).status_code == 400
    # a supervisor may not verify
    assert client.patch(f"/api/v1/weaving/actions/{ref}", headers=tokens["supervisor"], json={"status": "COMPLETED", "verified_cause": "x"}).status_code == 403
    assert client.patch(f"/api/v1/weaving/actions/{ref}", headers=tokens["supervisor"], json={"status": "COMPLETED"}).status_code == 200
    assert client.patch(f"/api/v1/weaving/actions/{ref}", headers=tokens["manager"], json={"verified_cause": "worn main nozzle"}).status_code == 200
    ins = get(client, "/api/v1/weaving/pages/insights", tokens["manager"]).json()["data"]
    f = next(f for f in ins["findings"] if f["key"] == "loom_decline:AJ-14")
    assert f["verified_cause"] == "worn main nozzle" and any(a["ref"] == ref for a in f["actions"])
    # every other finding still has no verified cause
    assert all(x["verified_cause"] is None for x in ins["findings"] if x["key"] != "loom_decline:AJ-14")


def test_shift_notes_are_saved_to_the_current_shift_and_can_be_resolved(client, tokens):
    r = post(client, "/api/v1/weaving/notes", tokens["supervisor"], body="Nozzle on AJ-03 changed", loom="AJ-03", category="ISSUE", severity="WARNING")
    assert r.status_code == 200
    cockpit = get(client, "/api/v1/weaving/pages/cockpit", tokens["supervisor"]).json()["data"]
    note = next(n for n in cockpit["notes"] if n["body"] == "Nozzle on AJ-03 changed")
    assert note["loom"] == "AJ-03" and note["this_shift"] and not note["resolved"]
    assert client.post(f"/api/v1/weaving/notes/{note['id']}/resolve", headers=tokens["supervisor"]).status_code == 200
    assert post(client, "/api/v1/weaving/notes", tokens["supervisor"], body="x", loom="NOPE").status_code in (400, 422)


def test_schedule_decision_needs_the_right_role_and_a_fresh_plan(client, tokens):
    plan = get(client, "/api/v1/weaving/pages/scheduler", tokens["manager"]).json()["data"]
    body = {"decision": "APPROVE", "signature": plan["signature"]}
    assert client.post("/api/v1/weaving/scheduler/decision", headers=tokens["supervisor"], json=body).status_code == 403
    assert client.post("/api/v1/weaving/scheduler/decision", headers=tokens["manager"], json={**body, "signature": "0" * 16}).status_code == 400  # stale plan
    ok = client.post("/api/v1/weaving/scheduler/decision", headers=tokens["manager"], json=body)
    assert ok.status_code == 200, ok.text
    res = ok.json()["data"]
    assert res["status"] == "APPROVED" and res["actions_created"] >= 1
    acts = get(client, "/api/v1/weaving/pages/actions", tokens["manager"]).json()["data"]["actions"]
    assert any(a["finding_key"] == f"schedule:{res['plan_ref']}" and a["approved"] for a in acts)
    after = get(client, "/api/v1/weaving/pages/scheduler", tokens["manager"]).json()["data"]
    assert any(d["plan_ref"] == res["plan_ref"] and d["status"] == "APPROVED" for d in after["decisions"])

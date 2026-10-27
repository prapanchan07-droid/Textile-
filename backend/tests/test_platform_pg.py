"""Imports, analytics, alerts, telemetry, work and reports against PostgreSQL (TEST_DATABASE_URL)."""
import hashlib
import os
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from app.mill.alerts import engine
from app.mill.analytics import pages
from app.mill.analytics.records import Filters, load
from app.mill.importers.service import ImportRefused, commit, import_file, preview
from app.mill.models import (
    Alert, AlertRule, AuditLog, Group, GroupLoomAssignment, ImportBatch, Loom, MachineConnection, Notification, RawSourceRow, ShiftProduction,
)
from app.mill.reports.owner import build_snapshot
from app.mill.seed import bootstrap_groups, ensure_defaults
from app.mill.telemetry.collector import collect_once, live_state
from tests import grids

pytestmark = pytest.mark.pg


@pytest.fixture(autouse=True)
def _uploads(tmp_path, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))


def _workbook(days=(1,), eff_b=None) -> bytes:
    sheets = []
    for d in days:
        ty = grids.ty_sheet(f"{d:02d}.09.26-TY")
        if eff_b is not None:
            ty.rows[3][8] = eff_b  # L02 shift B efficiency
        sheets += [ty, grids.sz_sheet(f"{d:02d}.09.26-SZ")]
    return grids.to_xlsx(sheets)


# ------------------------------------------------------------------ imports


def test_import_preview_commit_and_traceability(db):
    content = _workbook()
    b = preview(db, content, "sept.xlsx", None)
    assert b.status == "PREVIEWED" and b.summary["plan"] == {"insert": 15, "update": 0, "unchanged": 0, "new_looms": 5}
    assert db.scalar(select(func.count()).select_from(ShiftProduction)) == 0  # preview writes no production data
    commit(db, b)
    assert db.scalar(select(func.count()).select_from(ShiftProduction)) == 15
    rec = db.scalar(select(ShiftProduction).join(Loom).where(Loom.code == "TY-01", ShiftProduction.shift == "A"))
    raw = db.get(RawSourceRow, rec.raw_row_id)
    assert raw.sheet == "01.09.26-TY" and raw.row == 3 and raw.cells[0] == "L01"
    assert rec.batch_id == b.id
    with open(b.stored_path, "rb") as f:
        assert hashlib.sha256(f.read()).hexdigest() == b.sha256  # original kept byte-for-byte
    assert db.scalar(select(Loom.width_cm).where(Loom.code == "TY-01")) == 340
    sz = db.scalar(select(ShiftProduction).join(Loom).where(Loom.code == "SZ-01").limit(1))
    assert sz.warp_stops is None


def test_same_file_twice_is_refused_and_overlap_updates_in_place(db):
    import_file(db, _workbook(), "a.xlsx")
    with pytest.raises(ImportRefused):
        import_file(db, _workbook(), "a-copy.xlsx")
    db.rollback()
    b = import_file(db, _workbook(eff_b=88.5), "b.xlsx")  # one value revised
    assert (b.records_inserted, b.records_updated, b.records_unchanged) == (0, 1, 14)
    assert db.scalar(select(func.count()).select_from(ShiftProduction)) == 15
    rec = db.scalar(select(ShiftProduction).join(Loom).where(Loom.code == "TY-02", ShiftProduction.shift == "B"))
    assert rec.efficiency_pct == 88.5
    assert b.summary["data_quality"]["issues"].get("INFO:REVISED") == 1  # the change is recorded, not silent


def test_pick_and_mtr_fill_the_same_records(db):
    import_file(db, grids.to_xlsx(grids.tsudakoma_sheets("x100 picks")), "13-PICK.xlsx")
    b = import_file(db, grids.to_xlsx(grids.tsudakoma_sheets("meter")), "13-MTR.xlsx")
    assert b.records_inserted == 0 and b.records_updated == 3
    rows = list(db.scalars(select(ShiftProduction)))
    assert len(rows) == 3 and all(r.kilopicks is not None and r.meters is not None for r in rows)


def test_unreadable_file_fails_visibly(db):
    b = preview(db, b"not a spreadsheet", "x.xlsx", None)
    assert b.status == "FAILED" and b.error


# ------------------------------------------------------------------ analytics


def test_group_membership_is_by_date(db):
    import_file(db, _workbook(days=(1, 2)), "two-days.xlsx")
    ensure_defaults(db)
    g1, g2 = bootstrap_groups(db, 2)
    loom = db.scalar(select(Loom).where(Loom.code == "TY-01"))
    db.add(GroupLoomAssignment(group_id=g1.id, loom_id=loom.id, valid_from=date(2026, 8, 1), valid_to=date(2026, 9, 2)))
    db.add(GroupLoomAssignment(group_id=g2.id, loom_id=loom.id, valid_from=date(2026, 9, 2)))
    db.flush()
    in_g1 = load(db, Filters(group_id=g1.id))
    in_g2 = load(db, Filters(group_id=g2.id))
    assert {r["prod_date"] for r in in_g1} == {date(2026, 9, 1)}
    assert {r["prod_date"] for r in in_g2} == {date(2026, 9, 2)}


def test_mill_report_preferred_and_sources_labelled(db):
    import_file(db, _workbook(), "sept.xlsx")
    loom = db.scalar(select(Loom).where(Loom.code == "TY-01"))
    db.add(ShiftProduction(loom_id=loom.id, prod_date=date(2026, 9, 1), shift="A", source_kind="MACHINE_EXPORT", efficiency_pct=50.0, extras={}))
    db.flush()
    rows = [r for r in load(db, Filters(loom_ids=[loom.id])) if r["shift"] == "A"]
    assert len(rows) == 1 and rows[0]["source_kind"] == "MILL_REPORT" and rows[0]["efficiency_pct"] == 84.0
    only = load(db, Filters(loom_ids=[loom.id], source="MACHINE_EXPORT"))
    assert [r["efficiency_pct"] for r in only] == [50.0]


def test_command_center_states_its_basis(db):
    import_file(db, _workbook(), "sept.xlsx")
    cc = pages.command_center(db, Filters(date_from=date(2026, 9, 1), date_to=date(2026, 9, 1)))
    k = cc["kpis"]
    assert k["registered_looms"] == 5 and k["reporting_looms"] == 5 and k["loom_shifts"] == 15
    assert k["meters"] == pytest.approx(sum([120, 130, 125, 285, 275, 218, 257, 274, 222, 114.07, 113.03, 102.75, 22.89, 22.33, 17.22]), abs=0.01)
    assert cc["freshness"]["live_feed"] == "NONE" and "not a live machine feed" in cc["freshness"]["statement"]
    assert set(cc["by_category"]) == {"TY", "SZ"} and cc["by_category"]["SZ"]["warp_stops"] is None


# ------------------------------------------------------------------ alerts


def _eff_rows(db, effs):
    """One TY loom with consecutive shift efficiencies (A, B, C per day) from the mill report."""
    loom = Loom(code="TY-09", category="TY", loom_no=9, manufacturer="Toyota", attributes={})
    db.add(loom)
    db.flush()
    d = date(2026, 9, 1)
    for i, e in enumerate(effs):
        db.add(ShiftProduction(loom_id=loom.id, prod_date=d + timedelta(days=i // 3), shift="ABC"[i % 3], source_kind="MILL_REPORT",
                               efficiency_pct=e, kilopicks=500.0, meters=250.0, warp_stops=2, weft_stops=5, extras={}))
    db.flush()
    return loom


def _only(db, code):
    for r in db.scalars(select(AlertRule)):
        r.enabled = r.code == code
    db.flush()


def test_alert_needs_consecutive_breaches_and_deduplicates(db):
    ensure_defaults(db)
    _only(db, "EFF_LOW")  # < 80 for 2 shifts
    _eff_rows(db, [90, 90, 75])
    engine.evaluate_all(db)
    assert db.scalar(select(func.count()).select_from(Alert)) == 0  # one bad shift is not enough
    db.query(ShiftProduction).delete()
    db.query(Loom).delete()
    _eff_rows(db, [90, 75, 74])
    engine.evaluate_all(db)
    engine.evaluate_all(db)  # re-evaluating the same data changes nothing
    alerts = list(db.scalars(select(Alert)))
    assert len(alerts) == 1 and alerts[0].status == "OPEN" and alerts[0].occurrences == 1 and alerts[0].period_label == "2026-09-01 C"
    assert alerts[0].evidence["records"][-1]["value"] == 74
    assert db.scalar(select(func.count()).select_from(Notification)) == 0  # no users in this test database yet


def test_alert_lifecycle_refresh_clear_resolve_and_no_reopen_of_history(db):
    ensure_defaults(db)
    _only(db, "EFF_LOW")
    loom = _eff_rows(db, [75, 74])
    engine.evaluate_all(db)
    a = db.scalar(select(Alert))
    db.add(ShiftProduction(loom_id=loom.id, prod_date=date(2026, 9, 1), shift="C", source_kind="MILL_REPORT", efficiency_pct=73.0, extras={}))
    db.flush()
    engine.evaluate_all(db)
    db.refresh(a)
    assert a.occurrences == 2 and a.period_label == "2026-09-01 C"
    for i, s in enumerate("AB"):
        db.add(ShiftProduction(loom_id=loom.id, prod_date=date(2026, 9, 2), shift=s, source_kind="MILL_REPORT", efficiency_pct=92.0, extras={}))
    db.flush()
    engine.evaluate_all(db)
    db.refresh(a)
    assert a.condition_cleared_at is not None and a.status == "OPEN"  # cleared, but a person resolves it
    a.status, a.resolved_at, a.resolution_notes = "RESOLVED", datetime.now(timezone.utc) - timedelta(days=3), "Beam changed"
    db.flush()
    engine.evaluate_all(db)
    assert db.scalar(select(func.count()).select_from(Alert)) == 1  # history does not re-trigger


def test_cooldown_and_escalation(db):
    ensure_defaults(db)
    _only(db, "EFF_CRITICAL")  # < 60, 1 shift, escalate after 8 h
    loom = _eff_rows(db, [50])
    engine.evaluate_all(db)
    a = db.scalar(select(Alert))
    a.status, a.resolved_at, a.resolution_notes = "RESOLVED", datetime.now(timezone.utc), "ok"
    db.add(ShiftProduction(loom_id=loom.id, prod_date=date(2026, 9, 1), shift="B", source_kind="MILL_REPORT", efficiency_pct=40.0, extras={}))
    db.flush()
    stats = engine.evaluate_all(db)
    assert stats["cooldown"] == 1 and db.scalar(select(func.count()).select_from(Alert)) == 1
    a.resolved_at = datetime.now(timezone.utc) - timedelta(days=2)
    db.flush()
    engine.evaluate_all(db)
    new = db.scalar(select(Alert).where(Alert.status == "OPEN"))
    assert new is not None and new.id != a.id
    assert engine.escalate(db, now=datetime.now(timezone.utc) + timedelta(hours=9)) == 1
    db.refresh(new)
    assert new.escalation_level == 1
    assert engine.escalate(db, now=datetime.now(timezone.utc) + timedelta(hours=10)) == 0  # once per interval


def test_notification_failure_does_not_stop_evaluation(db, monkeypatch):
    from app.mill.alerts import notify

    ensure_defaults(db)
    _only(db, "EFF_CRITICAL")
    _eff_rows(db, [50])
    monkeypatch.setattr(notify, "select", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("mail server down")))
    engine.evaluate_all(db)
    assert db.scalar(select(func.count()).select_from(Alert)) == 1


# ------------------------------------------------------------------ telemetry


def test_simulator_readings_are_marked_and_staleness_is_shown(db):
    from app.mill.models import TelemetrySample

    loom = Loom(code="TY-01", category="TY", loom_no=1, manufacturer="Toyota", attributes={})
    db.add(loom)
    db.flush()
    conn = MachineConnection(loom_id=loom.id, adapter="SIMULATOR", enabled=True, state="CONFIGURED", poll_seconds=60)
    db.add(conn)
    db.flush()
    assert live_state(conn) == "OFFLINE"  # enabled but never read: not healthy
    now = datetime.now(timezone.utc)
    assert collect_once(db, now) == {"ok": 1}
    s = db.scalar(select(TelemetrySample))
    assert s.data_origin == "SIMULATED"
    assert live_state(conn, now) == "CONNECTED"
    assert live_state(conn, now + timedelta(minutes=30)) == "STALE"


def test_vendor_adapters_never_pretend_to_connect(db):
    loom = Loom(code="TS-01", category="TS", loom_no=1, manufacturer="Tsudakoma", attributes={})
    db.add(loom)
    db.flush()
    conn = MachineConnection(loom_id=loom.id, adapter="TSUDAKOMA_TISS", host="10.0.0.5", enabled=True, state="CONFIGURED")
    db.add(conn)
    db.flush()
    assert collect_once(db) == {"not_ready": 1}
    assert conn.state == "AWAITING_VENDOR_INFO" and live_state(conn) == "AWAITING_VENDOR_INFO" and conn.last_success_at is None


def test_stale_connection_raises_an_alert(db):
    ensure_defaults(db)
    _only(db, "TELEMETRY_STALE")
    loom = Loom(code="TY-02", category="TY", loom_no=2, manufacturer="Toyota", attributes={})
    db.add(loom)
    db.flush()
    db.add(MachineConnection(loom_id=loom.id, adapter="SIMULATOR", enabled=True, state="CONNECTED",
                             last_success_at=datetime.now(timezone.utc) - timedelta(hours=1)))
    db.flush()
    engine.evaluate_all(db)
    assert db.scalar(select(Alert.rule_code)) == "TELEMETRY_STALE"


# ------------------------------------------------------------------ API: auth, tasks, reports


@pytest.fixture()
def client(db):
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        tok = c.post("/api/v1/auth/login", json={"username": "admin", "password": "Ashok@2026"}).json()["data"]["access_token"]
        c.headers["Authorization"] = f"Bearer {tok}"
        yield c


def test_api_requires_sign_in(client):
    from fastapi.testclient import TestClient

    from app.main import app

    assert TestClient(app).get("/api/v1/mill/dashboard").status_code == 401
    assert client.get("/api/v1/mill/dashboard").status_code == 200


def test_task_workflow_and_audit(client, db):
    g = client.post("/api/v1/mill/groups/bootstrap?count=11").json()["data"]
    assert len(g) == 11
    t = client.post("/api/v1/mill/tasks", json={"title": "Check beam on TY-04", "group_id": g[0]["id"], "priority": "HIGH"}).json()["data"]
    assert t["status"] == "PENDING"
    assert client.patch(f"/api/v1/mill/tasks/{t['id']}", json={"status": "COMPLETED"}).status_code == 400  # needs completion notes
    assert client.patch(f"/api/v1/mill/tasks/{t['id']}", json={"status": "BLOCKED"}).status_code == 400  # needs a reason
    client.patch(f"/api/v1/mill/tasks/{t['id']}", json={"status": "IN_PROGRESS"})
    done = client.patch(f"/api/v1/mill/tasks/{t['id']}", json={"status": "COMPLETED", "completion_notes": "Beam re-gaited"}).json()["data"]
    assert done["status"] == "COMPLETED" and done["completed_at"]
    assert [e["to"] for e in done["events"] if e["kind"] == "STATUS"] == ["IN_PROGRESS", "COMPLETED"]
    assert client.patch(f"/api/v1/mill/tasks/{t['id']}", json={"status": "PENDING"}).status_code == 400
    db.expire_all()
    actions = {a.action for a in db.scalars(select(AuditLog))}
    assert {"GROUPS_BOOTSTRAP", "TASK_CREATE", "TASK_UPDATE"} <= actions


def test_loom_reassignment_keeps_history(client, db):
    client.post("/api/v1/mill/imports/preview", files={"file": ("s.xlsx", _workbook(), "application/octet-stream")})
    batch = db.scalar(select(ImportBatch))
    client.post(f"/api/v1/mill/imports/{batch.id}/commit")
    db.expire_all()
    assert db.get(ImportBatch, batch.id).status == "COMMITTED"
    g = client.post("/api/v1/mill/groups/bootstrap?count=2").json()["data"]
    loom = db.scalar(select(Loom).where(Loom.code == "TY-01"))
    client.post(f"/api/v1/mill/groups/{g[0]['id']}/looms", json={"loom_ids": [loom.id], "effective_from": "2026-08-01"})
    client.post(f"/api/v1/mill/groups/{g[1]['id']}/looms", json={"loom_ids": [loom.id], "effective_from": "2026-09-15"})
    rows = list(db.scalars(select(GroupLoomAssignment).order_by(GroupLoomAssignment.valid_from)))
    assert [(r.group_id, r.valid_from, r.valid_to) for r in rows] == [(g[0]["id"], date(2026, 8, 1), date(2026, 9, 15)), (g[1]["id"], date(2026, 9, 15), None)]


def test_report_snapshot_is_frozen_at_publication(client, db):
    import_file(db, _workbook(), "sept.xlsx")
    db.commit()
    r = client.post("/api/v1/mill/reports", json={"period_start": "2026-09-01", "period_end": "2026-09-01"}).json()["data"]
    meters = r["snapshot"]["production"]["meters"]
    assert client.post(f"/api/v1/mill/reports/{r['id']}/publish").status_code == 400  # commentary required
    client.patch(f"/api/v1/mill/reports/{r['id']}", json={"commentary": "Steady day."})
    assert client.post(f"/api/v1/mill/reports/{r['id']}/publish").json()["data"]["status"] == "PUBLISHED"
    import_file(db, _workbook(eff_b=50.0), "revised.xlsx")  # later data changes the underlying records
    db.commit()
    again = client.get(f"/api/v1/mill/reports/{r['id']}").json()["data"]
    assert again["snapshot"]["production"]["meters"] == meters and again["snapshot"] == r["snapshot"]
    assert client.post(f"/api/v1/mill/reports/{r['id']}/refresh").status_code == 400
    x = client.get(f"/api/v1/mill/reports/{r['id']}/export.xlsx")
    assert x.status_code == 200 and x.content[:2] == b"PK"
    fresh = build_snapshot(db, date(2026, 9, 1), date(2026, 9, 1))
    assert fresh["efficiency"]["by_shift"]["B"] != r["snapshot"]["efficiency"]["by_shift"]["B"]


def test_owner_report_uses_selected_period(db):
    import_file(db, _workbook(days=(1, 2)), "two.xlsx")
    one = build_snapshot(db, date(2026, 9, 2), date(2026, 9, 2))
    both = build_snapshot(db, date(2026, 9, 1), date(2026, 9, 2))
    assert one["production"]["loom_shifts"] == 15 and both["production"]["loom_shifts"] == 30
    assert both["meta"]["period"] == {"from": "2026-09-01", "to": "2026-09-02", "shift": None}


def test_group_bootstrap_only_once(db):
    assert len(bootstrap_groups(db, 11)) == 11
    assert bootstrap_groups(db, 11) == []
    assert db.scalar(select(func.count()).select_from(Group)) == 11


@pytest.mark.skipif(not os.environ.get("MILL_SAMPLE_DIR"), reason="MILL_SAMPLE_DIR not set (folder with the mill's real report files)")
def test_real_files_reconcile(db):
    """Optional: import the mill's actual files and require their own totals to reconcile (except known source issues)."""
    d = os.environ["MILL_SAMPLE_DIR"]
    for name in sorted(os.listdir(d)):
        if name.lower().endswith((".xls", ".xlsx")):
            with open(os.path.join(d, name), "rb") as f:
                b = import_file(db, f.read(), name)
            assert b.status == "COMMITTED" and b.error_count == 0, name

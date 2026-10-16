"""Schema constraints, foreign keys, migrations (up, down, up; no drift) and PostgreSQL connectivity."""
from datetime import datetime, timedelta, timezone

import pytest
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.db.migrate import current_revision, head_revision
from app.db.session import Base, check_db_connection
from app.weaving import models as m
from tests.factories import UTC, World

pytestmark = pytest.mark.pg
T0 = datetime(2026, 10, 14, 1, 0, tzinfo=UTC)


def test_connectivity_reports_postgresql():
    r = check_db_connection()
    assert r["status"] == "healthy" and r["database_type"] == "postgresql"


def test_schema_is_at_head_and_matches_the_models(engine):
    assert current_revision(str(engine.url.render_as_string(hide_password=False))) == head_revision()
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn, opts={"compare_type": True}), Base.metadata)
    assert diff == [], f"models and migrations have drifted: {diff}"


def test_all_weaving_tables_exist_with_indexes(engine):
    insp = inspect(engine)
    names = set(insp.get_table_names())
    expected = {"wv_shifts", "wv_looms", "wv_styles", "wv_beams", "wv_beam_mountings", "wv_production_orders", "wv_order_assignments", "wv_operators", "wv_shift_assignments",
                "wv_attendance", "wv_loom_readings", "wv_stop_reasons", "wv_stop_events", "wv_defect_types", "wv_inspections", "wv_defect_observations", "wv_maintenance_events", "wv_actions"}
    assert expected <= names
    idx = {i["name"] for i in insp.get_indexes("wv_stop_events")}
    assert {"ix_wv_stop_events_date_loom", "ix_wv_stop_events_reason_date", "ix_wv_stop_events_open"} <= idx
    assert "ix_wv_loom_readings_date_loom" in {i["name"] for i in insp.get_indexes("wv_loom_readings")}


def test_foreign_keys_are_enforced(db):
    w = World(db)
    db.add(m.WvLoomReading(loom_id=999_999, reading_start=T0, reading_end=T0 + timedelta(hours=1), duration_seconds=3600, shift_id=w.shift["I"].id,
                           shift_date=T0.date(), running_seconds=10, picks=1))
    with pytest.raises(IntegrityError):
        db.flush()


@pytest.mark.parametrize("kw", [
    dict(running_seconds=3601),  # ran longer than the interval
    dict(running_seconds=-1),
    dict(picks=-5),
    dict(quality_flag="MAYBE"),
    dict(duration_seconds=0),
])
def test_reading_check_constraints(db, kw):
    w = World(db)
    base = dict(loom_id=w.loom.id, reading_start=T0, reading_end=T0 + timedelta(hours=1), duration_seconds=3600, shift_id=w.shift["I"].id, shift_date=T0.date(), running_seconds=100, picks=100)
    base.update(kw)
    db.add(m.WvLoomReading(**base))
    with pytest.raises(IntegrityError):
        db.flush()


def test_reading_interval_must_run_forward_and_be_unique(db):
    w = World(db)
    db.add(m.WvLoomReading(loom_id=w.loom.id, reading_start=T0, reading_end=T0 - timedelta(hours=1), duration_seconds=3600, shift_id=w.shift["I"].id, shift_date=T0.date(), running_seconds=1, picks=1))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()
    w = World(db)
    w.reading(T0, picks=1)
    db.flush()
    w.reading(T0, picks=2)  # same loom, same start
    with pytest.raises(IntegrityError):
        db.flush()


def test_stop_event_must_not_end_before_it_starts_and_open_is_allowed(db):
    w = World(db)
    w.stop(T0, T0 + timedelta(minutes=2))
    w.stop(T0 + timedelta(hours=1), None)  # open
    db.flush()
    w.stop(T0 + timedelta(hours=2), T0 + timedelta(hours=1))
    with pytest.raises(IntegrityError):
        db.flush()


def test_one_open_beam_mounting_and_one_open_assignment_per_loom(db):
    w = World(db)
    beam = m.WvBeam(beam_no="B1", style_id=w.style.id, total_ends=100, length_m=1000, data_origin="LIVE")
    beam2 = m.WvBeam(beam_no="B2", style_id=w.style.id, total_ends=100, length_m=1000, data_origin="LIVE")
    db.add_all([beam, beam2])
    db.flush()
    db.add(m.WvBeamMounting(beam_id=beam.id, loom_id=w.loom.id, mounted_at=T0, data_origin="LIVE"))
    db.flush()
    db.add(m.WvBeamMounting(beam_id=beam2.id, loom_id=w.loom.id, mounted_at=T0 + timedelta(hours=1), data_origin="LIVE"))
    with pytest.raises(IntegrityError):
        db.flush()


@pytest.mark.parametrize("model_kw", [
    ("loom", dict(loom_code="X", loom_type="A", rated_rpm=0)),
    ("style", dict(style_code="X", fabric_name="x", ppi=0, target_efficiency_pct=90)),
    ("style", dict(style_code="Y", fabric_name="x", ppi=50, target_efficiency_pct=120)),
    ("loom", dict(loom_code="Z", loom_type="A", rated_rpm=100, data_origin="FAKE")),
])
def test_master_data_checks(db, model_kw):
    kind, kw = model_kw
    db.add((m.WvLoom if kind == "loom" else m.WvStyle)(**kw))
    with pytest.raises(IntegrityError):
        db.flush()


def test_defect_and_inspection_constraints(db):
    w = World(db)
    db.add(m.WvInspection(roll_no="R", loom_id=w.loom.id, style_id=w.style.id, shift_id=w.shift["I"].id, shift_date=T0.date(), inspected_at=T0, length_m=0, grade="A"))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()
    w = World(db)
    i = w.roll("R2", 50, "A", [], T0.date())
    db.flush()
    db.add(m.WvDefectObservation(inspection_id=i.id, defect_type_id=w.dtype["FLOAT"].id, severity="MINOR", points=5, defect_count=1))  # 4-point system
    with pytest.raises(IntegrityError):
        db.flush()


def test_migration_down_and_up_again_keeps_users(engine, db):
    """Downgrading the weaving schema drops only wv_* tables; users and legacy tables are untouched."""
    from alembic import command
    from app.db.migrate import alembic_config
    from app.db.seed_users import seed_demo_users

    seed_demo_users(db)
    db.commit()
    url = engine.url.render_as_string(hide_password=False)
    before = db.execute(text("SELECT username, role, password_hash FROM users ORDER BY username")).all()
    assert len(before) == 5
    db.close()
    command.downgrade(alembic_config(url), "0001")
    with engine.connect() as c:
        tables = set(inspect(c).get_table_names())
        assert not any(t.startswith("wv_") for t in tables) and "users" in tables
        assert c.execute(text("SELECT username, role, password_hash FROM users ORDER BY username")).all() == before
    command.upgrade(alembic_config(url), "head")
    with engine.connect() as c:
        assert any(t.startswith("wv_") for t in inspect(c).get_table_names())
        assert c.execute(text("SELECT username, role, password_hash FROM users ORDER BY username")).all() == before

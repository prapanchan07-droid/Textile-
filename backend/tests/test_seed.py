"""The demonstration seed: deterministic, idempotent, non-destructive, clearly labelled, never in production."""
import hashlib
from datetime import timedelta

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.weaving import models as m
from app.weaving.seed.demo import seed_demo
from app.weaving.seed.reference import ensure_reference_data
from tests.conftest import truncate_all
from tests.factories import FIXED_NOW

pytestmark = pytest.mark.pg


def table_counts(db):
    return {t: db.scalar(text(f"SELECT count(*) FROM {t}")) for t in ("wv_looms", "wv_beams", "wv_loom_readings", "wv_stop_events", "wv_inspections", "wv_defect_observations", "wv_maintenance_events", "wv_shift_assignments", "wv_attendance")}


def fingerprint(db) -> str:
    h = hashlib.sha256()
    for q in ("SELECT loom_id, reading_start, running_seconds, picks, quality_flag FROM wv_loom_readings ORDER BY loom_id, reading_start",
              "SELECT loom_id, started_at, ended_at, reason_id FROM wv_stop_events ORDER BY loom_id, started_at",
              "SELECT roll_no, grade, length_m FROM wv_inspections ORDER BY roll_no"):
        for row in db.execute(text(q)):
            h.update(repr(tuple(row)).encode())
    return h.hexdigest()


def test_seed_is_idempotent(db):
    r1 = seed_demo(db, now=FIXED_NOW, days=10)
    db.commit()
    first = table_counts(db)
    assert first["wv_looms"] == 32 and first["wv_loom_readings"] > 5000 and first["wv_stop_events"] > 1000
    r2 = seed_demo(db, now=FIXED_NOW, days=10)
    db.commit()
    assert table_counts(db) == first
    assert all(v == 0 for v in r2.added.values()), r2.added
    assert r1.epoch == r2.epoch


def test_seed_is_deterministic(db, engine):
    seed_demo(db, now=FIXED_NOW, days=7)
    db.commit()
    a = fingerprint(db)
    db.rollback()  # end this session's transaction so TRUNCATE is not blocked by its own read lock
    truncate_all(engine)
    with Session(engine) as s2:
        seed_demo(s2, now=FIXED_NOW, days=7)
        s2.commit()
        assert fingerprint(s2) == a


def test_extending_history_only_adds_rows(db):
    seed_demo(db, now=FIXED_NOW, days=7)
    db.commit()
    before = fingerprint(db)
    first_readings = db.scalar(text("SELECT count(*) FROM wv_loom_readings"))
    old_rows = db.execute(text("SELECT loom_id, reading_start, picks FROM wv_loom_readings ORDER BY loom_id, reading_start")).all()
    seed_demo(db, now=FIXED_NOW + timedelta(days=3), days=7)  # 3 days later: same epoch, longer history
    db.commit()
    assert db.scalar(text("SELECT count(*) FROM wv_loom_readings")) > first_readings
    kept = db.execute(text("SELECT loom_id, reading_start, picks FROM wv_loom_readings ORDER BY loom_id, reading_start")).all()
    assert set(old_rows) <= set(kept), "history that was already there must not change"


def test_seed_never_touches_existing_records(db):
    """A real (LIVE) loom and style already in the database are left exactly as they were."""
    db.add(m.WvLoom(loom_code="AJ-01", loom_type="Airjet", make="REAL MAKE", rated_rpm=777, data_origin="LIVE"))
    db.add(m.WvStyle(style_code="S-101", fabric_name="REAL FABRIC", ppi=99, target_efficiency_pct=80, data_origin="LIVE"))
    db.commit()
    seed_demo(db, now=FIXED_NOW, days=5)
    db.commit()
    loom = db.scalar(select(m.WvLoom).where(m.WvLoom.loom_code == "AJ-01"))
    style = db.scalar(select(m.WvStyle).where(m.WvStyle.style_code == "S-101"))
    assert (loom.make, loom.rated_rpm, loom.data_origin) == ("REAL MAKE", 777, "LIVE")
    assert (style.fabric_name, float(style.ppi), style.data_origin) == ("REAL FABRIC", 99.0, "LIVE")


def test_everything_seeded_is_labelled_demo(db):
    seed_demo(db, now=FIXED_NOW, days=5)
    db.commit()
    for t in ("wv_looms", "wv_styles", "wv_beams", "wv_loom_readings", "wv_stop_events", "wv_inspections", "wv_maintenance_events", "wv_actions", "wv_operators"):
        assert db.scalar(text(f"SELECT count(*) FROM {t} WHERE data_origin <> 'DEMO'")) == 0, t


def test_seed_refuses_production(db, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    with pytest.raises(RuntimeError, match="production"):
        seed_demo(db, now=FIXED_NOW, days=3)
    assert db.scalar(text("SELECT count(*) FROM wv_looms")) == 0


def test_seeded_data_satisfies_its_own_constraints_and_covers_the_requirements(db):
    seed_demo(db, now=FIXED_NOW, days=14)
    db.commit()
    assert 24 <= db.scalar(select(func.count()).select_from(m.WvLoom)) <= 40
    assert db.scalar(select(func.count()).select_from(m.WvShift)) == 3
    assert db.scalar(select(func.count()).select_from(m.WvStyle)) >= 4
    assert db.scalar(select(func.count()).select_from(m.WvBeam)) >= 24
    assert db.scalar(select(func.count()).select_from(m.WvProductionOrder)) >= 4
    cats = {r[0] for r in db.execute(text("SELECT DISTINCT r.category FROM wv_stop_events e JOIN wv_stop_reasons r ON r.id = e.reason_id"))}
    assert {"WARP", "WEFT", "MECHANICAL", "ELECTRICAL"} <= cats
    assert db.scalar(text("SELECT count(DISTINCT defect_type_id) FROM wv_defect_observations")) >= 5
    # the overnight shift has readings that cross midnight in mill time, kept on the day the shift started
    night = db.execute(text("SELECT count(*) FROM wv_loom_readings r JOIN wv_shifts s ON s.id = r.shift_id WHERE s.code = 'III'")).scalar()
    assert night > 0
    assert db.scalar(text("SELECT count(*) FROM wv_stop_events WHERE ended_at IS NULL")) >= 0  # open stops are allowed


def test_reference_data_is_insert_if_missing_only(db):
    ensure_reference_data(db)
    db.commit()
    db.execute(text("UPDATE wv_stop_reasons SET name = 'Edited by the mill' WHERE code = 'WARP_BREAK'"))
    db.commit()
    again = ensure_reference_data(db)
    db.commit()
    assert again == {"shifts": 0, "stop_reasons": 0, "defect_types": 0}
    assert db.scalar(text("SELECT name FROM wv_stop_reasons WHERE code = 'WARP_BREAK'")) == "Edited by the mill"

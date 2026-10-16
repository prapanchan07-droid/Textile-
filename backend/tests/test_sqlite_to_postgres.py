"""Moving the legacy SQLite database into PostgreSQL: complete, validated, non-destructive and repeatable."""
import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from app.db.session import Base
from app.db.sqlite_to_postgres import migrate
import app.db.models_registry  # noqa: F401

pytestmark = pytest.mark.pg

HASH = "pbkdf2_sha256$240000$c2FsdHNhbHRzYWx0$aGFzaGhhc2hoYXNoaGFzaGhhc2g="


@pytest.fixture()
def sqlite_file(tmp_path: Path) -> Path:
    """A legacy-shaped database: the pre-weaving tables only, with users, reports and records."""
    path = tmp_path / "legacy.db"
    eng = create_engine(f"sqlite:///{path}")
    legacy = [t for t in Base.metadata.sorted_tables if not t.name.startswith("wv_")]
    Base.metadata.create_all(eng, tables=legacy)
    with eng.begin() as c:
        c.execute(text("INSERT INTO users (id, username, full_name, role, password_hash, is_active, created_at) VALUES "
                       "('u1','owner','Gokul','OWNER',:h,1,'2026-01-01 00:00:00'),('u2','quality','Priya','QUALITY',:h2,1,'2026-01-02 00:00:00'),('u3','retired','Old','QUALITY',:h,0,'2026-01-03 00:00:00')"),
                  {"h": HASH, "h2": HASH + "x"})
        c.execute(text("INSERT INTO reports (id, file_hash, filename, file_path, report_type, confidence_score, status, report_date, upload_timestamp) "
                       "VALUES ('r1','abc','a.csv','/x/a.csv','PRODUCTION',0.9,'PROCESSED','2026-10-01','2026-10-02 10:00:00')"))
        c.execute(text("INSERT INTO production_records (id, source_report_id, report_date, machine_id, actual_kg, target_kg, gap_kg, achievement_pct, created_at) "
                       "VALUES ('p1','r1','2026-10-01','M1',90,100,10,90,'2026-10-02 10:00:00'),('p2','r1','2026-10-01','M2',80,100,20,80,'2026-10-02 10:00:00')"))
    eng.dispose()
    return path


def pg_url(engine) -> str:
    return engine.url.render_as_string(hide_password=False)


def counts(engine):
    with engine.connect() as c:
        return {t: c.execute(text(f"SELECT count(*) FROM {t}")).scalar() for t in ("users", "reports", "production_records")}


def test_copy_preserves_users_hashes_roles_and_records(engine, db, sqlite_file, tmp_path):
    db.close()
    from tests.conftest import truncate_all
    truncate_all(engine)
    report = migrate(sqlite_file, pg_url(engine), tmp_path / "bk")
    assert report.ok and report.committed, report.problems
    assert counts(engine) == {"users": 3, "reports": 1, "production_records": 2}
    with engine.connect() as c:
        rows = {r.username: r for r in c.execute(text("SELECT username, role, password_hash, is_active FROM users"))}
    assert rows["owner"].password_hash == HASH and rows["owner"].role == "OWNER"
    assert rows["quality"].password_hash == HASH + "x" and rows["quality"].role == "QUALITY"
    assert rows["retired"].is_active is False
    # a verified backup of the source was written first
    assert report.backup_path.exists() and report.backup_sha256 and report.backup_path != sqlite_file
    bk = sqlite3.connect(report.backup_path)
    assert bk.execute("SELECT count(*) FROM users").fetchone()[0] == 3


def test_source_file_is_not_modified(engine, db, sqlite_file, tmp_path):
    db.close()
    from tests.conftest import truncate_all
    import hashlib
    truncate_all(engine)
    before = hashlib.sha256(sqlite_file.read_bytes()).hexdigest()
    migrate(sqlite_file, pg_url(engine), tmp_path / "bk")
    assert hashlib.sha256(sqlite_file.read_bytes()).hexdigest() == before


def test_running_it_twice_inserts_nothing_the_second_time(engine, db, sqlite_file, tmp_path):
    db.close()
    from tests.conftest import truncate_all
    truncate_all(engine)
    migrate(sqlite_file, pg_url(engine), tmp_path / "bk")
    again = migrate(sqlite_file, pg_url(engine), tmp_path / "bk")
    assert again.ok and all(t.inserted == 0 for t in again.tables) and counts(engine) == {"users": 3, "reports": 1, "production_records": 2}


def test_dry_run_writes_nothing(engine, db, sqlite_file, tmp_path):
    db.close()
    from tests.conftest import truncate_all
    truncate_all(engine)
    report = migrate(sqlite_file, pg_url(engine), tmp_path / "bk", dry_run=True)
    assert report.ok and not report.committed
    assert counts(engine) == {"users": 0, "reports": 0, "production_records": 0}


def test_existing_postgres_rows_are_never_overwritten_and_the_copy_rolls_back(engine, db, sqlite_file, tmp_path):
    """The target already has a user with the same username but a different password hash: that must survive, and the run must fail validation."""
    db.close()
    from tests.conftest import truncate_all
    truncate_all(engine)
    with engine.begin() as c:
        c.execute(text("INSERT INTO users (id, username, full_name, role, password_hash, is_active, created_at) VALUES ('other','owner','Different','OWNER','DIFFERENT-HASH',true,now())"))
    report = migrate(sqlite_file, pg_url(engine), tmp_path / "bk")
    assert not report.ok and not report.committed
    assert any("owner" in p for p in report.problems) or any("missing" in p for p in report.problems)
    with engine.connect() as c:
        assert c.execute(text("SELECT password_hash FROM users WHERE username='owner'")).scalar() == "DIFFERENT-HASH"
        assert c.execute(text("SELECT count(*) FROM users")).scalar() == 1  # nothing else was written: the whole copy rolled back


def test_refuses_a_missing_source_and_a_non_postgres_target(engine, tmp_path):
    with pytest.raises(FileNotFoundError):
        migrate(tmp_path / "nope.db", pg_url(engine), tmp_path)
    f = tmp_path / "x.db"
    sqlite3.connect(f).close()
    with pytest.raises(ValueError):
        migrate(f, "sqlite:///other.db", tmp_path)

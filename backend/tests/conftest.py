"""
Test setup.

PostgreSQL tests need a DEDICATED test database: set TEST_DATABASE_URL to a PostgreSQL URL whose database
name ends in `_test` (the suite drops and recreates that database's `public` schema). Without it those
tests are skipped, and the pure-logic tests (parsers, metric formulas) still run. The suite never
reads DATABASE_URL, so it cannot touch the application's data.
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

TEST_URL = os.environ.get("TEST_DATABASE_URL", "")
# app.core.config insists on a database being configured when it is imported.
os.environ["DATABASE_URL"] = TEST_URL or "sqlite://"
os.environ["ENVIRONMENT"] = "development"
os.environ["AUTO_MIGRATE"] = "true"
os.environ["SEED_DEMO_USERS"] = "true"
os.environ["BACKGROUND_JOBS_ENABLED"] = "false"

from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402


def _is_safe(url: str) -> bool:
    u = make_url(url)
    return u.get_backend_name() == "postgresql" and (u.database or "").endswith("_test")


def pytest_collection_modifyitems(config, items):
    if TEST_URL and _is_safe(TEST_URL):
        return
    reason = "TEST_DATABASE_URL not set" if not TEST_URL else "TEST_DATABASE_URL must be PostgreSQL and its database name must end in _test"
    skip = pytest.mark.skip(reason=reason)
    for item in items:
        if "pg" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def engine():
    from app.db.migrate import upgrade_to_head

    eng = create_engine(TEST_URL)
    with eng.begin() as c:
        c.execute(text("DROP SCHEMA public CASCADE"))
        c.execute(text("CREATE SCHEMA public"))
    upgrade_to_head(TEST_URL)
    yield eng
    eng.dispose()


def truncate_all(engine) -> None:
    with engine.begin() as c:
        names = [r[0] for r in c.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename <> 'alembic_version'"))]
        if names:
            c.execute(text("TRUNCATE " + ", ".join(f'"{n}"' for n in names) + " RESTART IDENTITY CASCADE"))


@pytest.fixture()
def db(engine):
    """A clean database (all tables empty, schema at head) for one test."""
    truncate_all(engine)
    with Session(engine) as session:
        yield session
        session.rollback()

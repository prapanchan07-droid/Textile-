"""Run Alembic from code: used at API start-up (dev), by the SQLite->PostgreSQL tool and by tests."""
from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine

BACKEND_DIR = Path(__file__).resolve().parents[2]


def alembic_config(url: Optional[str] = None) -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    if url:
        cfg.cmd_opts = type("Opts", (), {"x": [f"url={url}"]})()  # read back by alembic/env.py
    return cfg


def head_revision() -> str:
    return ScriptDirectory.from_config(alembic_config()).get_current_head()


def current_revision(url: str) -> Optional[str]:
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            return MigrationContext.configure(conn).get_current_revision()
    finally:
        engine.dispose()


def upgrade_to_head(url: Optional[str] = None) -> None:
    command.upgrade(alembic_config(url), "head")

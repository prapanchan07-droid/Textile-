"""Importing this module registers every table on ``Base.metadata`` (used by Alembic, init and tests)."""
import app.models.user  # noqa: F401
import app.mill.models  # noqa: F401

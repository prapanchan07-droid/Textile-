"""Importing this module registers every table on ``Base.metadata`` (used by Alembic, init and tests)."""
import app.models.system  # noqa: F401
import app.models.user  # noqa: F401
import app.models.ingestion  # noqa: F401
import app.models.template_data  # noqa: F401
import app.weaving.models  # noqa: F401

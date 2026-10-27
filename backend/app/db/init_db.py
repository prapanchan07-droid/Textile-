from app.db.session import SessionLocal
from app.db.migrate import current_revision, head_revision, upgrade_to_head
import app.db.models_registry  # noqa: F401
from app.db.seed_users import seed_demo_users
from app.mill.seed import ensure_defaults
from app.core.config import settings
from app.core.logging import logger


def init_db():
    """Bring the schema to the latest Alembic revision (dev), or verify it (production), then seed defaults."""
    if settings.AUTO_MIGRATE:
        logger.info("Applying database migrations...")
        upgrade_to_head()
    else:
        current, head = current_revision(settings.DATABASE_URL), head_revision()
        if current != head:
            raise RuntimeError(f"Database schema is at {current!r} but the code expects {head!r}. Run `alembic upgrade head`.")

    db = SessionLocal()
    try:
        seed_demo_users(db)
        ensure_defaults(db)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing DB seed data: {str(e)}")
    finally:
        db.close()

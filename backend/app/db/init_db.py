from datetime import datetime
import uuid
from app.db.session import SessionLocal
from app.db.migrate import current_revision, head_revision, upgrade_to_head
from app.models.system import SystemInfo, ModuleRegistry
import app.db.models_registry  # noqa: F401
from app.db.seed_users import seed_demo_users
from app.weaving.seed.reference import ensure_reference_data
from app.core.config import settings
from app.core.logging import logger

def init_db():
    """Bring the schema to the latest Alembic revision (dev), or verify it (production), then seed reference data."""
    if settings.AUTO_MIGRATE:
        logger.info("Applying database migrations...")
        upgrade_to_head()
    else:
        current, head = current_revision(settings.DATABASE_URL), head_revision()
        if current != head:
            raise RuntimeError(f"Database schema is at {current!r} but the code expects {head!r}. Run `alembic upgrade head`.")
    
    db = SessionLocal()
    try:
        # Seed version if not present
        version_entry = db.query(SystemInfo).filter(SystemInfo.key == "schema_version").first()
        if not version_entry:
            db.add(SystemInfo(
                id=str(uuid.uuid4()),
                key="schema_version",
                value=settings.VERSION,
                description="Database schema version"
            ))
            db.add(SystemInfo(
                id=str(uuid.uuid4()),
                key="company_name",
                value=settings.COMPANY_NAME,
                description="Company name"
            ))
            
            # Module 01 registration
            db.add(ModuleRegistry(
                id=str(uuid.uuid4()),
                module_number="MODULE_01",
                name="Project architecture and environment",
                phase="PHASE_1_FOUNDATION",
                is_active=True,
                installed_at=datetime.utcnow()
            ))
            
            db.commit()
            logger.info("Initial system metadata & Module 01 seeded successfully.")
        seed_demo_users(db)
        if db.bind is not None and db.bind.dialect.name == 'postgresql':
            ensure_reference_data(db)
            db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing DB seed data: {str(e)}")
    finally:
        db.close()

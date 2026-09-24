from datetime import datetime
import uuid
from app.db.session import engine, Base, SessionLocal
from app.models.system import SystemInfo, ModuleRegistry
import app.models.ingestion  # noqa: F401
from app.core.config import settings
from app.core.logging import logger

def init_db():
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    
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
    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing DB seed data: {str(e)}")
    finally:
        db.close()

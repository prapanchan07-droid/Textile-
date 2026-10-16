from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import settings
from app.db.session import Base
import app.db.models_registry  # noqa: F401  (imports every model so Base.metadata is complete)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _url() -> str:
    # `alembic -x url=...` lets tests and the SQLite->PostgreSQL tool target another database.
    return context.get_x_argument(as_dictionary=True).get("url") or settings.DATABASE_URL


def _include_object(obj, name, type_, reflected, compare_to):
    """`alembic -x exclude_prefix=wv_ revision --autogenerate` keeps the weaving tables out of a revision (used to split 0001/0002)."""
    prefix = context.get_x_argument(as_dictionary=True).get("exclude_prefix")
    table = name if type_ == "table" else getattr(getattr(obj, "table", None), "name", None)
    return not (prefix and table and table.startswith(prefix))


def run_migrations_offline() -> None:
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True, compare_type=True, include_object=_include_object)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True, include_object=_include_object)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

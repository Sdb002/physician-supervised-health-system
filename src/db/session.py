"""Engine and session factory. SQLite by default; swap via DATABASE_URL."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import settings

_MIGRATIONS = Path(__file__).resolve().parent / "migrations"

_connect_args = {}
if settings.database_url.startswith("sqlite"):
    _connect_args["check_same_thread"] = False

engine = create_engine(settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def migration_config(target: Engine | None = None) -> Config:
    """Alembic's configuration for `target` (default: the app's database)."""
    config = Config()
    config.set_main_option("script_location", str(_MIGRATIONS))
    config.attributes["engine"] = target or engine
    return config


def init_db(target: Engine | None = None) -> None:
    """Bring the database to the current schema: create it if it is new, and
    apply whatever migrations it has not had yet (src/db/migrations). A
    database made before migrations existed is adopted by the baseline."""
    command.upgrade(migration_config(target), "head")

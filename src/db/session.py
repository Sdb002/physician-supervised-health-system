"""Engine and session factory. SQLite by default; swap via DATABASE_URL."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import settings
from src.db.models import Base

_connect_args = {}
if settings.database_url.startswith("sqlite"):
    _connect_args["check_same_thread"] = False

engine = create_engine(settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """Create all tables. For schema evolution beyond the thesis, move to Alembic
    (see src/db/migrations/README.md)."""
    Base.metadata.create_all(engine)

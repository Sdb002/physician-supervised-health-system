"""Alembic environment: migrates the database the app is configured for.

init_db() hands over its own engine; from the command line the engine comes
from the app settings (DATABASE_URL), so both always act on the same database.
"""

from alembic import context

from src.db.models import Base

target_metadata = Base.metadata

if context.is_offline_mode():
    raise SystemExit("offline (--sql) migrations are not supported: run against the database")

engine = context.config.attributes.get("engine")
if engine is None:
    from src.db.session import engine

with engine.connect() as connection:
    # batch mode: SQLite cannot alter a column in place
    context.configure(connection=connection, target_metadata=target_metadata,
                      render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()

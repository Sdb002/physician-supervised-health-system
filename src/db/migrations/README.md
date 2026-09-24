# Migrations

The project currently uses `Base.metadata.create_all()` (see `src/db/session.py`),
which is sufficient for SQLite during development: it creates missing tables and
never alters existing ones.

When the schema needs to evolve against a database with real data, switch to
Alembic:

```
pip install alembic
alembic init src/db/migrations
# set sqlalchemy.url in alembic.ini (or read from src.core.config.settings)
# set target_metadata = src.db.models.Base.metadata in env.py
alembic revision --autogenerate -m "baseline"
alembic upgrade head
```

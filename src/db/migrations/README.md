# Migrations

The schema is managed with Alembic. The app applies pending migrations itself
at startup (`init_db()` in `src/db/session.py`), so pulling new code and
starting the API is all an existing database needs.

A database made before migrations existed (by `Base.metadata.create_all()`)
is adopted automatically: the baseline migration creates only the tables that
are missing, then the later ones run as usual.

## Changing the schema

1. Change the model in `src/db/models.py`.
2. Write the migration:

   ```
   .venv\Scripts\python.exe -m alembic revision -m "what changed"
   ```

   and fill in `upgrade()` / `downgrade()` in the new file under `versions/`.
   Number it after the last one (`0003_...`) and use `op.batch_alter_table`
   for changes to existing tables: SQLite cannot alter a column in place.
   A column added to a table that already holds rows must be nullable or
   carry a `server_default`.
3. Start the API, or run `.venv\Scripts\python.exe -m alembic upgrade head`.

`tests/test_migrations.py` checks that a migrated database has the schema the
models describe, so a model change without a migration fails the suite.

Both the app and the command line act on the database in `DATABASE_URL`.

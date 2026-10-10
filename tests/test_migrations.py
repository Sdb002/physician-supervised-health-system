"""Schema migrations: a migrated database matches the models, and a database
made before migrations existed is adopted without losing a row."""

import json

from alembic import command
from sqlalchemy import create_engine, inspect, text

from src.db.models import Base
from src.db.session import init_db, migration_config


def _engine(tmp_path, name="app.db"):
    return create_engine(f"sqlite:///{(tmp_path / name).as_posix()}")


def _schema(engine) -> dict:
    inspector = inspect(engine)
    return {
        table: {c["name"]: bool(c["nullable"]) for c in inspector.get_columns(table)}
        for table in inspector.get_table_names() if table != "alembic_version"
    }


def test_a_new_database_gets_the_schema_the_models_describe(tmp_path):
    # a model change without a migration fails here
    migrated = _engine(tmp_path)
    init_db(migrated)
    expected = _engine(tmp_path, "models.db")
    Base.metadata.create_all(expected)
    assert _schema(migrated) == _schema(expected)


def test_migrating_twice_changes_nothing(tmp_path):
    engine = _engine(tmp_path)
    init_db(engine)
    before = _schema(engine)
    init_db(engine)
    assert _schema(engine) == before


def test_a_database_from_before_migrations_is_adopted_with_its_rows(tmp_path):
    engine = _engine(tmp_path)
    # the old schema, with no record of any migration: what create_all() left
    command.upgrade(migration_config(engine), "0001")
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE alembic_version"))
        connection.execute(text(
            "INSERT INTO patients (id, name, sex, birth_year, height_cm, pregnant, "
            "conditions, fitness_level, notes, created_at) VALUES "
            "(1, 'Ayesha', 'female', 1990, 158, 0, :conditions, 'beginner', '', "
            "'2026-01-01 00:00:00')"
        ), {"conditions": json.dumps(["anemia"])})

    init_db(engine)

    assert _schema(engine)["patients"]["activity_level"] is True
    with engine.connect() as connection:
        row = connection.execute(text(
            "SELECT name, conditions, dietary_restrictions, activity_level, "
            "pregnancy_trimester FROM patients"
        )).one()
    assert row.name == "Ayesha" and json.loads(row.conditions) == ["anemia"]
    assert json.loads(row.dietary_restrictions) == []
    assert row.activity_level is None and row.pregnancy_trimester is None

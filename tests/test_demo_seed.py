"""The synthetic demo data: seeded once, into an empty database only, and a
hosted demo's start-up (SEED_DEMO_DATA) survives a second instance seeding
at the same moment."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.api import main
from src.core.config import Settings
from src.db import demo
from src.db.models import Assessment, AuditLog, Patient, User


def test_the_demo_patients_and_logins_are_seeded_once(db_session):
    assert demo.seed_demo(db_session, report=lambda line: None) is True
    patients = db_session.scalars(select(Patient)).all()
    assert len(patients) == 4
    assert {a.status for a in db_session.scalars(select(Assessment))} == {"pending"}
    emails = {u.email for u in db_session.scalars(select(User))}
    assert {"doctor@health.local", "pending.doctor@health.local", "patient@health.local"} <= emails
    # the demo doctor's patients, each seeding on the audit log
    doctor = db_session.scalars(select(User).where(User.email == "doctor@health.local")).one()
    assert {p.doctor_id for p in patients} == {doctor.id}
    assert len(db_session.scalars(select(AuditLog).where(AuditLog.action == "patient.seed")).all()) == 4

    # a database with patients is left alone
    assert demo.seed_demo(db_session, report=lambda line: None) is False
    assert len(db_session.scalars(select(Patient)).all()) == 4


def test_on_vercel_without_a_database_the_api_says_so(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
        main.check_hosted_database(Settings(database_url="sqlite:///./health.db"))
    main.check_hosted_database(Settings(database_url="postgres://u:p@db.example/neondb"))
    monkeypatch.delenv("VERCEL")
    main.check_hosted_database(Settings(database_url="sqlite:///./health.db"))  # a local run


def test_a_postgres_url_as_hosts_give_it_gets_the_installed_driver():
    for given in ("postgres://u:p@db.example/neondb?sslmode=require",
                  "postgresql://u:p@db.example/neondb?sslmode=require"):
        expected = "postgresql+psycopg://u:p@db.example/neondb?sslmode=require"
        assert Settings(database_url=given).database_url == expected
    assert Settings(database_url="sqlite:///./x.db").database_url == "sqlite:///./x.db"


def test_startup_leaves_the_seeding_to_the_instance_that_won(monkeypatch):
    def lost_the_race(db, actor, report):
        raise IntegrityError("INSERT INTO users", {}, Exception("duplicate email"))

    monkeypatch.setattr(demo, "seed_demo", lost_the_race)
    main.seed_demo_data()  # no exception: the other instance seeded it

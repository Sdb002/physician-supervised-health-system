import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.deps import get_db
from src.api.main import app
from src.core.security import create_token, hash_password
from src.db.models import Base, User
from src.diet import recommender


@pytest.fixture(autouse=True)
def _no_trained_model(monkeypatch):
    """Pin the whole suite to the deterministic scoring fallback by default.

    Without this, tests/test_deficiency_match.py, tests/test_meal_plan.py and
    tests/test_recipe_ranking.py (which assert exact deterministic-formula
    properties) would pass only by accident of whether the trained models in
    data/models/ happen to exist on whoever's machine is running pytest —
    true once the training script has ever been run locally.
    tests/test_recommender.py overrides this per-test via monkeypatch (last
    set wins).
    """
    monkeypatch.setattr(recommender, "load_model", lambda: None)
    monkeypatch.setattr(recommender, "load_recipe_model", lambda: None)


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    # workflow routes are staff-only: authenticate the client as a doctor,
    # and expose admin/patient credentials for tests that need other roles
    setup = TestSession()
    doctor = User(email="doctor@test.local", password_hash=hash_password("password123"),
                  name="Dr Test", role="doctor", status="active")
    admin = User(email="admin@test.local", password_hash=hash_password("password123"),
                 name="Admin Test", role="admin", status="active")
    setup.add_all([doctor, admin])
    setup.commit()
    doctor_id, admin_id = doctor.id, admin.id
    setup.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        test_client.headers.update(
            {"Authorization": f"Bearer {create_token(doctor_id, 'doctor')}"}
        )
        test_client.admin_headers = {
            "Authorization": f"Bearer {create_token(admin_id, 'admin')}"
        }
        yield test_client
    app.dependency_overrides.clear()

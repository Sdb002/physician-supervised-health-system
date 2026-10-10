"""The API refuses to start a deployment on the auth settings published in the
README, and only warns about them on a developer's machine."""

import logging

import pytest

from src.api.main import check_published_defaults
from src.core.config import Settings


def _settings(**overrides) -> Settings:
    # _env_file=None: the developer's own .env must not decide these tests
    return Settings(_env_file=None, **{
        "database_url": "sqlite:///./health.db",
        "cors_origins": "http://localhost:3000",
        "environment": "development",
        "secret_key": "dev-secret-change-me",
        "admin_password": "admin12345",
        **overrides,
    })


def test_defaults_only_warn_on_a_developers_machine(caplog):
    with caplog.at_level(logging.WARNING):
        check_published_defaults(_settings())
    assert "SECRET_KEY and ADMIN_PASSWORD still at the published default" in caplog.text


@pytest.mark.parametrize("deployment", [
    {"environment": "production"},
    {"database_url": "postgresql+psycopg://health:health@db:5432/health"},
    {"cors_origins": "http://localhost:3000,https://clinic.example.org"},
])
def test_defaults_stop_a_deployment_from_starting(deployment):
    with pytest.raises(RuntimeError, match="refusing to start: SECRET_KEY and ADMIN_PASSWORD"):
        check_published_defaults(_settings(**deployment))


def test_each_default_is_named_on_its_own():
    with pytest.raises(RuntimeError, match="refusing to start: ADMIN_PASSWORD still"):
        check_published_defaults(_settings(environment="production", secret_key="x" * 48))


def test_a_deployment_with_its_own_secrets_starts(caplog):
    with caplog.at_level(logging.WARNING):
        check_published_defaults(_settings(
            environment="production", secret_key="x" * 48, admin_password="a-long-passphrase",
            database_url="postgresql+psycopg://health:health@db:5432/health",
            cors_origins="https://clinic.example.org",
        ))
    assert caplog.text == ""

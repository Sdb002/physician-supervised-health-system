"""Application settings and canonical filesystem paths."""

from pathlib import Path
from urllib.parse import urlsplit

from pydantic_settings import BaseSettings, SettingsConfigDict
from ruamel.yaml import YAML

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
REFERENCE_DIR = DATA_DIR / "reference"

_DEFAULT_DB = f"sqlite:///{(PROJECT_ROOT / 'health.db').as_posix()}"

# Published in .env.example and the README: fine on a developer's machine,
# an open door anywhere else.
DEFAULT_SECRET_KEY = "dev-secret-change-me"
DEFAULT_ADMIN_PASSWORD = "admin12345"
# as urlsplit().hostname gives them: an IPv6 address comes without its brackets
_LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = ""
    # who reads an uploaded lab slip: "local" (RapidOCR on this server, see
    # src/ocr), "claude" (needs ANTHROPIC_API_KEY, sends the image to
    # Anthropic) or "auto" (local when installed, else Claude when configured)
    ocr_engine: str = "auto"
    # the clinic's clock, for a patient's "today" in the daily task list:
    # Bangladesh Standard Time is UTC+6 all year (no daylight saving since 2009)
    clinic_utc_offset_hours: float = 6.0
    database_url: str = _DEFAULT_DB
    cors_origins: str = "http://localhost:3000"
    # "development" on a developer's machine; anything else is a deployment
    environment: str = "development"

    # auth — override all of these outside local development
    secret_key: str = DEFAULT_SECRET_KEY
    admin_email: str = "admin@health.local"
    admin_password: str = DEFAULT_ADMIN_PASSWORD
    admin_name: str = "Administrator"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_local(self) -> bool:
        """Whether this looks like a developer's machine: the development
        environment, a SQLite file, and a dashboard served from this host.
        Any one of those saying otherwise makes it a deployment."""
        browsers_are_local = all(
            urlsplit(origin).hostname in _LOCAL_HOSTS for origin in self.cors_origin_list
        )
        return (self.environment == "development"
                and self.database_url.startswith("sqlite")
                and browsers_are_local)

    def published_defaults(self) -> list[str]:
        """The auth settings still at their published values."""
        defaults = []
        if self.secret_key == DEFAULT_SECRET_KEY:
            defaults.append("SECRET_KEY")
        if self.admin_password == DEFAULT_ADMIN_PASSWORD:
            defaults.append("ADMIN_PASSWORD")
        return defaults


settings = Settings()


def load_yaml(path: Path) -> dict:
    yaml = YAML(typ="safe")
    with open(path, encoding="utf-8") as f:
        return yaml.load(f)

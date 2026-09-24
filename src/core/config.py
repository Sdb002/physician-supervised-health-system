"""Application settings and canonical filesystem paths."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from ruamel.yaml import YAML

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
REFERENCE_DIR = DATA_DIR / "reference"

_DEFAULT_DB = f"sqlite:///{(PROJECT_ROOT / 'health.db').as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = ""
    database_url: str = _DEFAULT_DB
    cors_origins: str = "http://localhost:3000"

    # auth — override all of these outside local development
    secret_key: str = "dev-secret-change-me"
    admin_email: str = "admin@health.local"
    admin_password: str = "admin12345"
    admin_name: str = "Administrator"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()


def load_yaml(path: Path) -> dict:
    yaml = YAML(typ="safe")
    with open(path, encoding="utf-8") as f:
        return yaml.load(f)

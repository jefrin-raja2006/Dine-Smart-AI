"""Central application settings, read from environment variables / backend/.env."""

import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("dinesmart")

# Only used outside production so local development "just works".
# Production refuses to start with this value (see load_settings).
_DEV_SECRET_KEY = "dev-only-insecure-secret-key-change-me-0123456789abcdef"

_DEFAULT_OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]


def _csv(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer, got {raw!r}") from exc


def _normalize_database_url(url: str) -> str:
    # Many hosts (Heroku, Render, Railway) hand out "postgres://..." URLs,
    # which SQLAlchemy 2.x does not accept.
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


@dataclass(frozen=True)
class Settings:
    environment: str
    database_url: str
    secret_key: str
    access_token_expire_minutes: int
    cors_origins: list[str]
    overpass_servers: list[str]
    nearby_cache_ttl_seconds: int
    login_max_failures: int
    login_window_seconds: int
    register_max_per_window: int
    register_window_seconds: int

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


def load_settings() -> Settings:
    environment = os.getenv("ENVIRONMENT", "development").strip().lower()

    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to backend/.env and "
            "set DATABASE_URL, e.g. "
            "postgresql://user:password@localhost:5432/dinesmart"
        )

    secret_key = os.getenv("SECRET_KEY", "").strip()
    if environment == "production":
        if len(secret_key) < 32 or secret_key == _DEV_SECRET_KEY:
            raise RuntimeError(
                "SECRET_KEY must be set to a random string of at least 32 "
                "characters when ENVIRONMENT=production. Generate one with: "
                "python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
    elif not secret_key:
        secret_key = _DEV_SECRET_KEY
        logger.warning(
            "SECRET_KEY is not set - using an insecure development key. "
            "Set SECRET_KEY in backend/.env before deploying."
        )

    return Settings(
        environment=environment,
        database_url=_normalize_database_url(database_url),
        secret_key=secret_key,
        access_token_expire_minutes=_int("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24),
        cors_origins=_csv(
            os.getenv("CORS_ORIGINS"),
            ["http://localhost:5173", "http://127.0.0.1:5173"],
        ),
        overpass_servers=_csv(
            os.getenv("OVERPASS_SERVERS"), _DEFAULT_OVERPASS_SERVERS
        ),
        nearby_cache_ttl_seconds=_int("NEARBY_CACHE_TTL_SECONDS", 300),
        login_max_failures=_int("LOGIN_MAX_FAILURES", 5),
        login_window_seconds=_int("LOGIN_WINDOW_SECONDS", 15 * 60),
        register_max_per_window=_int("REGISTER_MAX_PER_WINDOW", 20),
        register_window_seconds=_int("REGISTER_WINDOW_SECONDS", 60 * 60),
    )


settings = load_settings()

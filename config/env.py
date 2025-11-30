"""
Environment loader for Django.

This module centralizes:
- Secure environment variable access
- Strong typing & validation
- Defaults for dev, strict requirements for staging/prod
- Namespaces for DB, Redis, Mail, AWS, Django settings, etc.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Literal


# ================================================
# Helpers
# ================================================
def _get(name: str, default=None, required: bool = False, cast=None):
    """
    Env getter:
    - required=True raises explicit error
    - cast applies type conversion (bool/int/etc.)
    - default only used when not required
    """
    raw = os.getenv(name, default)

    if required and (raw is None or raw == ""):
        raise RuntimeError(f"[env] Missing required environment variable: {name}")

    if cast and raw is not None:
        try:
            return cast(raw)
        except Exception:
            raise RuntimeError(f"[env] Failed to cast environment variable {name}={raw}")

    return raw


def _to_bool(value: str) -> bool:
    return value.lower() in ("1", "true", "yes", "y", "t")


# ================================================
# Environment selection
# ================================================
ENV: Literal["development", "staging", "production"] = _get(
    "DJANGO_ENV",
    default="development",
    cast=str
)


# ================================================
# Secrets
# ================================================
@dataclass(frozen=True)
class Secrets:
    SECRET_KEY: str = _get(
        "SECRET_KEY",
        default="dev-secret-key",
        required=(ENV in ("staging", "production"))
    )


# ================================================
# Database
# ================================================
@dataclass(frozen=True)
class Database:
    NAME: str = _get("DB_NAME", required=True)
    USER: str = _get("DB_USER", required=True)
    PASSWORD: str = _get("DB_PASS", required=True)
    HOST: str = _get("DB_HOST", required=True)
    PORT: str = _get("DB_PORT", default="5432")


# ================================================
# Redis
# ================================================
@dataclass(frozen=True)
class RedisConfig:
    URL_BASE: str = _get("REDIS_URL_BASE", required=True)
    DEFAULT: int = _get("REDIS_DB_DEFAULT", required=True)


# ================================================
# E-mail
# ================================================
@dataclass(frozen=True)
class Email:
    HOST: str = _get("EMAIL_HOST", required=(ENV == "production"))
    PORT: int = _get("EMAIL_PORT", default=587, cast=int)
    USER: Optional[str] = _get("EMAIL_HOST_USER")
    PASSWORD: Optional[str] = _get("EMAIL_HOST_PASSWORD")
    USE_TLS: bool = _get("EMAIL_USE_TLS", default="true", cast=_to_bool)


# ================================================
# AWS / Storage
# ================================================
@dataclass(frozen=True)
class AWS:
    ACCESS_KEY: Optional[str] = _get("AWS_ACCESS_KEY_ID")
    SECRET_KEY: Optional[str] = _get("AWS_SECRET_ACCESS_KEY")
    BUCKET: Optional[str] = _get("AWS_STORAGE_BUCKET_NAME")
    DOMAIN: Optional[str] = _get("AWS_S3_CUSTOM_DOMAIN")


# ================================================
# Django App Config
# ================================================
@dataclass(frozen=True)
class DjangoConfig:
    ALLOWED_HOSTS: list[str] = field(
        default_factory=lambda: _get("ALLOWED_HOSTS", default="").split(",") if _get("ALLOWED_HOSTS") else []
    )
    DEBUG: bool = (ENV == "development")


# ================================================
# Exported config
# ================================================
secrets = Secrets()
database = Database()
redis = RedisConfig()
email = Email()
aws = AWS()
django_conf = DjangoConfig()

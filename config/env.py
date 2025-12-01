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
    HOST: str = _get("REDIS_HOST", required=True)
    PORT: str = _get("REDIS_PORT", default="6379")
    PASSWORD: str = _get("REDIS_PASSWORD", required=True)
    DEFAULT_DB: int = _get("REDIS_DB_DEFAULT", required=True, cast=int)
    CELERY_DB: int = _get("REDIS_DB_CELERY", required=True, cast=int)

    @property
    def URL_BASE(self) -> str:
        return f"redis://:{self.PASSWORD}@{self.HOST}:{self.PORT}"


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
# Celery
# ================================================
@dataclass(frozen=True)
class CeleryConfig:
    redis: RedisConfig

    @property
    def BROKER_URL(self) -> str:
        return f"{self.redis.URL_BASE}/{self.redis.CELERY_DB}"

    @property
    def RESULT_BACKEND(self) -> str:
        return f"{self.redis.URL_BASE}/{self.redis.CELERY_DB}"

    TIMEZONE: str = _get("CELERY_TIMEZONE", required=True)
    ACCEPT_CONTENT: list[str] = field(
        default_factory=lambda: _get("CELERY_ACCEPT_CONTENT", default="json").split(",")
    )
    TASK_SERIALIZER: str = _get("CELERY_TASK_SERIALIZER", default="json")
    RESULT_SERIALIZER: str = _get("CELERY_RESULT_SERIALIZER", default="json")
    ENABLE_UTC: bool = _get("CELERY_ENABLE_UTC", default="true", cast=_to_bool)
    TASK_TRACK_STARTED: bool = _get("CELERY_TASK_TRACK_STARTED", default="true", cast=_to_bool)
    TASK_TIME_LIMIT: int = _get("CELERY_TASK_TIME_LIMIT", default=300, cast=int)
    BEAT_SCHEDULER: str = _get("CELERY_BEAT_SCHEDULER", required=True)

    BEAT_TZ_AWARE: bool = _get("DJANGO_CELERY_BEAT_TZ_AWARE", default="true", cast=_to_bool)


# ================================================
# Exported config
# ================================================
secrets = Secrets()
database = Database()
redis = RedisConfig()
email = Email()
aws = AWS()
django_conf = DjangoConfig()
celery = CeleryConfig(redis)

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
# Project
# ================================================
@dataclass(frozen=True)
class ProjectConfig:
    NAME: str = _get("PROJECT_NAME", required=True)
    URL: str = _get("PROJECT_URL", required=True)
    EMAIL: str = _get("PROJECT_EMAIL", required=True)


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
    USER: Optional[str] = _get("EMAIL_USER", default="")
    PASSWORD: Optional[str] = _get("EMAIL_PASSWORD", default="")
    USE_TLS: bool = _get("EMAIL_USE_TLS", default="true", cast=_to_bool)
    USE_SSL: bool = _get("EMAIL_USE_SSL", default="false", cast=_to_bool)
    TIMEOUT: int = _get("EMAIL_TIMEOUT", default=30, cast=int)
    CONNECTION_MAX_RETRIES: int = _get("EMAIL_CONNECTION_MAX_RETRIES", default=3, cast=int)
    BATCH_SIZE: int = _get("EMAIL_BATCH_SIZE", default=90, cast=int)
    MAX_ATTACHMENT_MB: int = _get("EMAIL_MAX_ATTACHMENT_MB", default=10, cast=int)
    DEFAULT_FROM: str = _get("DEFAULT_FROM_EMAIL", required=True)

    def __post_init__(self):
        if self.USE_TLS and self.USE_SSL:
            raise ValueError("EMAIL_USE_TLS and EMAIL_USE_SSL are mutually exclusive")


# ================================================
# AWS / Storage
# ================================================
@dataclass(frozen=True)
class AWS:
    ACCESS_KEY: Optional[str] = _get("AWS_ACCESS_KEY_ID", required=True)
    SECRET_KEY: Optional[str] = _get("AWS_SECRET_ACCESS_KEY", required=True)
    BUCKET_NAME: Optional[str] = _get("AWS_STORAGE_BUCKET_NAME", required=True)
    REGION_NAME: Optional[str] = _get("AWS_S3_REGION_NAME", required=True)
    STATIC_LOCATION: Optional[str] = _get("AWS_STATIC_LOCATION", required=True)
    MEDIA_LOCATION: Optional[str] = _get("AWS_MEDIA_LOCATION", required=True)

    @property
    def CUSTOM_DOMAIN(self) -> str:
        return f"{self.BUCKET_NAME}.s3.amazonaws.com"

    @property
    def STATIC_URL(self) -> str:
        return f"https://{self.CUSTOM_DOMAIN}/{self.STATIC_LOCATION}/"

    @property
    def MEDIA_URL(self) -> str:
        return f"https://{self.CUSTOM_DOMAIN}/{self.MEDIA_LOCATION}/"


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
# JWT
# ================================================
@dataclass(frozen=True)
class JWTConfig:
    ACCESS_TOKEN_LIFETIME_MINUTES: int = _get("JWT_ACCESS_LIFETIME_MINUTES", default="15", cast=int)
    REFRESH_TOKEN_LIFETIME_DAYS: int = _get("JWT_REFRESH_LIFETIME_DAYS", default="7", cast=int)
    ROTATE_REFRESH_TOKENS: bool = _get("JWT_ROTATE_REFRESH_TOKENS", default="true", cast=_to_bool)
    BLACKLIST_AFTER_ROTATION: bool = _get("JWT_BLACKLIST_AFTER_ROTATION", default="true", cast=_to_bool)


# ================================================
# Exported config
# ================================================
secrets = Secrets()
project = ProjectConfig()
database = Database()
redis = RedisConfig()
email = Email()
aws = AWS()
django_conf = DjangoConfig()
celery = CeleryConfig(redis)
jwt = JWTConfig()

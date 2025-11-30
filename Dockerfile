# ==============================================================
# BASE IMAGE
# ==============================================================
FROM python:3.10-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=2.0.0 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /usr/src/app

# ==============================================================
# SYSTEM DEPENDENCIES
# ==============================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install "poetry==$POETRY_VERSION"

# ==============================================================
# STAGE 1 — DEPENDENCIES
# ==============================================================
FROM base AS deps

# Enable virtual env inside container
RUN python -m venv /opt/venv

COPY pyproject.toml poetry.lock* ./

# Install dependencies WITHOUT dev tools
RUN . /opt/venv/bin/activate \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --without dev

# ==============================================================
# STAGE 2 — DEVELOPMENT IMAGE
# ==============================================================
FROM deps AS development

RUN . /opt/venv/bin/activate \
    && poetry install --no-interaction --no-ansi

COPY . .

ENV DJANGO_SETTINGS_MODULE=config.settings.development \
    DEBUG=1 \
    PORT=8000

EXPOSE ${PORT}

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# ==============================================================
# STAGE 3 — PRODUCTION IMAGE
# ==============================================================
FROM deps AS production

RUN groupadd -r appgroup && useradd -r -g appgroup appuser \
    && chown -R appuser:appgroup /usr/src/app

COPY --chown=appuser:appgroup . .

USER appuser

ENV DJANGO_SETTINGS_MODULE=config.settings.production \
    DEBUG=0 \
    PORT=8000

EXPOSE ${PORT}

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT}${HEALTHCHECK_PATH:-/health/} || exit 1

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]

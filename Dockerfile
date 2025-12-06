# ==============================================================
# BASE LAYER
# ==============================================================
FROM python:3.10-slim AS base

ARG BUILD_DATE=now

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VERSION=2.0.0 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /usr/src/app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        git \
        gettext \
        # Required for health checks and debugging
        iputils-ping \
        netcat-openbsd && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Poetry installation
RUN pip install "poetry==$POETRY_VERSION"

# ==============================================================
# DEPENDENCIES LAYER
# ==============================================================
FROM base AS dependencies

# Create virtual environment
RUN python -m venv /opt/venv

# Copy dependency definitions
COPY pyproject.toml poetry.lock* ./

# Install production dependencies
RUN . /opt/venv/bin/activate \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --without dev

# ==============================================================
# DEVELOPMENT LAYER
# ==============================================================
FROM dependencies AS development

# Install development dependencies
RUN . /opt/venv/bin/activate \
    && poetry install --no-interaction --no-ansi --with dev

# Copy application code
COPY . .

# Development-specific environment
ENV DJANGO_SETTINGS_MODULE=config.settings.development \
    DEBUG=1 \
    PORT=8000 \
    PYTHONPATH="/usr/src/app:$PYTHONPATH"

# Health check for development (proactive monitoring)
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Expose port (explicit contract)
EXPOSE ${PORT}

# Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# ==============================================================
# PRODUCTION LAYER
# ==============================================================
FROM dependencies AS production

# Non-root user for security
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -s /bin/false appuser && \
    chown -R appuser:appgroup /usr/src/app

# Copy application as non-root user
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser

# Production environment
ENV DJANGO_SETTINGS_MODULE=config.settings.production \
    DEBUG=False \
    PORT=8000

# Expose port (explicit contract)
EXPOSE ${PORT}

# Health check for production
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT}${HEALTHCHECK_PATH:-/health/} || exit 1

# Gunicorn for production
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]

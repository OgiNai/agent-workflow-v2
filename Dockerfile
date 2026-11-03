
# syntax=docker/dockerfile:1

# --------------------------------------------------
# Builder
# --------------------------------------------------
FROM python:3.12-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_CACHE_DIR=/root/.cache/uv

WORKDIR /app

RUN pip install --no-cache-dir uv==0.8.15

# Install dependencies from the lockfile.
COPY pyproject.toml uv.lock ./

RUN uv sync \
    --locked \
    --no-dev \
    --no-install-project

# --------------------------------------------------
# Production runtime
# --------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH" \
    PROJECT_PATH=/app \
    PORT=8080

WORKDIR /app

# Create a dedicated non-root application user.
RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && mkdir -p /app/workspace \
    && chown -R app:app /app/workspace

# Copy installed dependencies and application source.
COPY --from=builder --chown=app:app /app/.venv /app/.venv

COPY --chown=app:app apps/ ./apps/
COPY --chown=app:app alembic/ ./alembic/
COPY --chown=app:app alembic.ini ./

USER app

EXPOSE 8080

CMD ["sh", "-c", "exec uvicorn apps.main:code_app --host 0.0.0.0 --port ${PORT} --proxy-headers"]

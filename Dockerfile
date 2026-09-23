# syntax=docker/dockerfile:1.7

# Build the application and its locked dependencies with uv.
FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=0 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Install dependencies before copying the source so dependency layers remain cached.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock,readonly \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml,readonly \
    uv sync --locked --no-install-project

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Keep the runtime image free of uv and development dependencies.
FROM python:3.14-slim-trixie

# Use an uncommon fixed ID to avoid collisions with system groups in the base image.
RUN groupadd --system --gid 9999 nonroot \
    && useradd --gid 9999 --uid 9999 --create-home --shell /usr/sbin/nologin nonroot

COPY --from=builder --chown=nonroot:nonroot /app /app
RUN install -d --owner=nonroot --group=nonroot /app/db

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
USER nonroot

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

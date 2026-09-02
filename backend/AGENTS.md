# Repository Guidelines

## Project Structure & Module Organization

This repository contains a FastAPI authentication service. `app.py` creates the application, configures logging and lifecycle checks, mounts routers, and exposes root and health endpoints. Place endpoint modules in `routes/` (currently `routes/auth.py`), persistence adapters in `clients/`, and shared helpers in `utils/`. Cross-route FastAPI dependencies belong in `dependencies.py`. JSON-backed development data is stored in `db/`; treat user records and password hashes as sensitive. Dependency and tool configuration lives in `pyproject.toml`, with exact versions locked in `uv.lock`.

## Architecture Guidance for Agents

Agents must read `ARCHITECTURE.md` before adding or reorganizing features. Follow its flow and checklist. Update it when changes alter module responsibilities, request flow, persistence boundaries, or the standard feature pattern.

## Interface Design Guidance for Agents

Agents must read `DESIGN.md` before creating or changing HTML, CSS, visual components, layout,
or interaction states in `static/admin/`. Treat its token definitions and usage rules as the source
of truth for the admin identity. Reuse semantic CSS tokens instead of introducing literal colors,
spacing, radii, shadows, or timing values in component rules. If a visual requirement cannot be
expressed with an existing token, first verify that the value represents a reusable role or scale;
then update `DESIGN.md` and the corresponding CSS declarations together. Preserve documented
accessibility, focus, responsive, and reduced-motion behavior in every interface change.

## Build, Test, and Development Commands

- `uv sync --dev` installs the Python 3.14 environment and development tools from the lockfile.
- `uv run uvicorn app:app --reload --env-file .env` starts the API locally with auto-reload. Swagger UI is available under `/api/docs`.
- `uv run ruff check .` checks imports and the configured `E`, `F`, and `I` rules.
- `uv run ruff format --check .` verifies formatting; omit `--check` to apply it.
- `uv run ty check` runs static type checks.

Copy `.env.example` to `.env` and supply a strong `TOKEN_JWT` before starting the service. Never commit `.env` or real credentials.

## Coding Style & Naming Conventions

Use four-space indentation, type hints for public functions, and concise docstrings where behavior is not obvious. Ruff enforces a 100-character target line length, import sorting, and core Pyflakes/pycodestyle checks. Follow Python naming conventions: `snake_case` for functions and modules, `PascalCase` for Pydantic models, and `UPPER_SNAKE_CASE` for constants. Keep route handlers thin by moving reusable database or authentication logic into `clients/` or dependencies.

## Testing Guidelines

No automated test suite or coverage threshold is currently configured. New behavior should add `pytest` tests under `tests/`, using names such as `test_auth.py` and `test_invalid_token_returns_401`. Prefer FastAPI's `TestClient`, temporary JSON databases, and isolated environment variables. Once pytest is added to the dev dependencies, run tests with `uv run pytest`.

## Commit & Pull Request Guidelines

Recent commits use short, imperative Portuguese summaries (for example, `Adapta autenticação para banco JSON`). Keep each commit focused and match that style. Pull requests should explain the behavior change, list validation commands, link related issues, and call out environment or data-format changes. Include screenshots only when API documentation or another visible interface changes.

# Backend Architecture

## Overview

This project is a small, modular FastAPI application. Requests enter through the application in `app.py`, are delegated to an `APIRouter` in `routes/`, and use shared dependencies or persistence functions as needed.

```text
HTTP request
    -> app.py (application setup and router registration)
    -> routes/<feature>.py (validation, endpoint, response)
    -> dependencies.py (authentication/shared resources)
    -> clients/<resource>.py (JSON or external data access)
    -> db/*.json
```

The current authentication feature demonstrates this pattern:

- `app.py` registers `routes.auth.router`.
- `routes/auth.py` defines Pydantic models, authentication behavior, and `/auth` endpoints.
- `clients/db.py` reads user data from `db/users.json`.
- `dependencies.py` exposes reusable FastAPI dependencies and annotated aliases.
- `utils/` contains general-purpose time and logging helpers.

## Responsibilities by Module

### Application composition (`app.py`)

Keep global application concerns here: FastAPI configuration, lifespan startup checks, logging, middleware, health endpoints, and router registration. Do not add feature-specific business rules to this file.

### HTTP features (`routes/`)

Create one module per feature, such as `routes/schedule.py`. Each module should own its URL prefix, tags, request/response models, status codes, and endpoint orchestration. Hand data access to a client instead of opening JSON files directly.

### Persistence and integrations (`clients/`)

Client modules isolate storage and external-service details. Functions should accept explicit inputs and return plain dictionaries, lists, or typed domain values. Keeping file access here makes a future move from JSON to a database less disruptive.

### Shared dependencies (`dependencies.py`)

Use FastAPI dependencies for cross-cutting behavior such as JWT validation, authorization, configuration checks, and resource lifecycle. Prefer the existing `Annotated[..., Depends(...)]` aliases for concise endpoint signatures.

### Utilities (`utils/`)

Utilities must be framework-neutral and broadly reusable. Feature-specific helpers should stay in the feature module or move to a dedicated service module if the feature grows.

## Adding a Feature

For a new schedule feature backed by `db/schedule.json`:

1. Add `clients/schedule.py` with storage operations such as `list_events()` and `get_event(event_id)`. Keep path handling and JSON parsing inside this module.
2. Add `routes/schedule.py` with an `APIRouter`, Pydantic models, and handlers. Use dependency injection for protected endpoints.
3. Register the router in `app.py`.
4. Add tests in `tests/test_schedule.py`, covering successful responses, invalid input, missing records, and authorization failures.
5. Run `uv run ruff check .`, `uv run ruff format --check .`, `uv run ty check`, and, once pytest is configured, `uv run pytest`.

A minimal route follows the existing style:

```python
# routes/schedule.py
from typing import Annotated

from fastapi import APIRouter, Depends
from clients.schedule import list_events
from routes.auth import TokenData, get_token_data

router = APIRouter(prefix="/schedule", tags=["schedule"])

@router.get("")
async def read_schedule(
    token: Annotated[TokenData, Depends(get_token_data)],
) -> list[dict]:
    return list_events()
```

Register it at the composition root:

```python
from routes import auth, schedule

app.include_router(auth.router)
app.include_router(schedule.router)
```

If authentication is used by several new features, import `CurrentTokenData` from `dependencies.py` instead of repeating its `Annotated` declaration. Avoid importing a new route module from `dependencies.py`; that direction can create circular imports. Shared models or authentication primitives should move to a neutral module when reuse increases.

## Design Rules

- Keep endpoint functions thin: validate input, call feature/client logic, and shape the response.
- Use Pydantic models instead of untyped request or public response dictionaries.
- Raise `HTTPException` at the HTTP boundary; let client functions report missing data with `None` or a specific domain exception.
- Read secrets from environment variables and never store credentials in source or JSON fixtures.
- Add startup validation in the lifespan only for configuration required by the whole application.
- Preserve async endpoints, but do not mark ordinary synchronous file operations async unless an async storage client is introduced.

As a feature becomes complex, add `services/<feature>.py` between routes and clients for business rules. Introduce that layer only when logic is reused or no longer fits clearly in a route handler.

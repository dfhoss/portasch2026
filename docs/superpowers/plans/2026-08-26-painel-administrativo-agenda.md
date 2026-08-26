# Administrative Schedule Panel Implementation Plan

> **For executing agents:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to execute this plan task by task. The steps use checkboxes (`- [ ]`) for tracking.

**Objective:** Deliver an authenticated panel at `/admin`, independent of the public frontend, for editing the schedule, locations, and axes stored in JSON.

**Architecture:** FastAPI will serve plain HTML, CSS, and JavaScript and expose administrative APIs protected by `CurrentTokenData`. Pydantic models will validate the schedule; focused clients will encapsulate atomic reading and writing of the three JSON files. API tests will use temporary directories, and Playwright will validate real browser flows.

**Technical stack:** Python 3.14, FastAPI 0.141+, Pydantic, pytest, TestClient, Playwright for Python, HTML5, CSS, and framework-free JavaScript.

**Specification:** `docs/superpowers/specs/2026-08-26-painel-administrativo-agenda-design.md`

## Global constraints

- Do not modify or depend on the `frontend/` directory.
- Preserve the public format of `backend/db/schedule.json`, except for the approved migration of axes to Portuguese identifiers.
- Require a valid JWT for all schedule, location, and axis APIs; static HTML contains no administrative data.
- Keep the token only in `sessionStorage`.
- Generate and hide IDs; locations accept only `name` and receive `loc-NNN` IDs.
- Assume only one person edits at a time; do not add locking or versioning.
- Write JSON atomically and restore the previous data if an operation spanning two files fails.
- Use temporary copies of the JSON files in every test.
- Preserve the user's pre-existing changes in `backend/app.py`, `backend/routes/auth.py`, `backend/pyproject.toml`, and `backend/uv.lock`.

---

## File structure

- Create `backend/models/schedule.py`: Pydantic models and structural schedule validation.
- Create `backend/clients/json_store.py`: reusable atomic reading and replacement.
- Create `backend/clients/schedule.py`: schedule access and reference lookup/propagation.
- Create `backend/clients/locations.py`: CRUD for the simple location catalog.
- Create `backend/clients/knowledge_axes.py`: axis CRUD and migration.
- Create `backend/routes/admin.py`: serves the HTML document.
- Create `backend/routes/schedule.py`, `locations.py`, and `knowledge_axes.py`: authenticated APIs.
- Create `backend/static/admin/index.html`, `admin.css`, and `admin.js`: build-free panel.
- Create `backend/db/locations.json` and `knowledge_axes.json`: normalized initial data.
- Create `backend/tests/`: isolated model, client, route, and browser tests.
- Modify `backend/clients/db.py`: resolve `DATABASE_PATH` at call time to isolate authentication in tests.
- Modify `backend/app.py`: register routers and mount `/admin/static`.
- Modify `backend/pyproject.toml` and `backend/uv.lock`: add pytest without removing the already added Playwright.
- Modify `backend/ARCHITECTURE.md` and `backend/README.md`: document responsibilities and execution.

---

### Task 1: Test infrastructure and schedule models

**Files:**
- Modify: `backend/pyproject.toml`
- Mechanically modify: `backend/uv.lock`
- Create: `backend/models/__init__.py`
- Create: `backend/models/schedule.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_schedule_models.py`

**Interfaces:**
- Consumes: the current `db/schedule.json` format.
- Produces: `ScheduleDocument`, `Section`, `ScheduleGroup`, `Activity`, `Session`, and `slugify_id(value: str) -> str`.

- [ ] **Step 1: add pytest to the development group**

Preserve the existing `playwright>=1.62.0` and add:

```toml
[dependency-groups]
dev = [
    "ipykernel>=7.3.0",
    "playwright>=1.62.0",
    "pytest>=9.0.0",
    "ruff>=0.16.4",
    "ty>=0.0.74",
]
```

Run: `uv lock`

- [ ] **Step 2: write tests that express the schedule contract**

```python
from pydantic import ValidationError
from models.schedule import ScheduleDocument, slugify_id


def test_rejects_session_when_end_is_not_after_start():
    payload = {
        "version": 1,
        "eventDate": "2026-10-26",
        "sections": [{"id": "s", "title": "S", "groups": [{
            "id": "g", "title": "G", "items": [{"id": "a", "title": "A",
            "sessions": [{"startTime": "10:00", "endTime": "09:00", "location": "Sala"}]}]
        }]}],
    }
    with pytest.raises(ValidationError):
        ScheduleDocument.model_validate(payload)


def test_slugify_id_uses_portuguese_text_without_accents():
    assert slugify_id("Saúde e bem-estar") == "saude-e-bem-estar"
```

- [ ] **Step 3: run the tests and confirm the failure**

Run: `uv run pytest tests/test_schedule_models.py -v`

Expected: an import failure for `models.schedule`.

- [ ] **Step 4: implement models with JSON aliases**

```python
class Session(BaseModel):
    start_time: time = Field(alias="startTime")
    end_time: time = Field(alias="endTime")
    location: str | None = None

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def end_after_start(self) -> Self:
        if self.end_time <= self.start_time:
            raise ValueError("O horário final deve ser posterior ao inicial")
        return self


class ScheduleDocument(BaseModel):
    version: int = Field(ge=1)
    event_date: date = Field(alias="eventDate")
    sections: list[Section]

    model_config = ConfigDict(populate_by_name=True)
```

Implement the intermediate models with the existing optional fields and validation of unique IDs throughout the document. `slugify_id` uses `unicodedata.normalize`, lowercase letters, hyphens, and a numeric suffix when the caller detects a collision.

- [ ] **Step 5: run tests, lint, and type checks**

Run:

```powershell
uv run pytest tests/test_schedule_models.py -v
uv run ruff check models tests/test_schedule_models.py
uv run ty check
```

Expected: all pass.

- [ ] **Step 6: commit**

```powershell
git add pyproject.toml uv.lock models tests/conftest.py tests/test_schedule_models.py
git commit -m "Adiciona modelos validados da agenda"
```

---

### Task 2: Atomic persistence and initial catalogs

**Files:**
- Create: `backend/clients/json_store.py`
- Create: `backend/clients/schedule.py`
- Create: `backend/clients/locations.py`
- Create: `backend/clients/knowledge_axes.py`
- Create: `backend/db/locations.json`
- Create: `backend/db/knowledge_axes.json`
- Modify: `backend/db/schedule.json`
- Create: `backend/tests/test_json_clients.py`

**Interfaces:**
- Consumes: `ScheduleDocument` and `slugify_id` from Task 1.
- Produces: `read_json(path: Path) -> dict`, `atomic_write_json(path: Path, payload: dict) -> None`, `load_schedule(path: Path) -> ScheduleDocument`, `save_schedule(document: ScheduleDocument, path: Path) -> None`, `get_schedule_path() -> Path`, `get_locations_path() -> Path`, `get_knowledge_axes_path() -> Path`, `LocationRepository`, and `KnowledgeAxisRepository`.

- [ ] **Step 1: write isolated persistence and CRUD tests**

```python
def test_location_ids_are_generated_and_not_reused(tmp_path):
    path = tmp_path / "locations.json"
    schedule_path = tmp_path / "schedule.json"
    path.write_text('{"nextId": 3, "locations": [{"id":"loc-002","name":"Hall"}]}')
    schedule_path.write_text('{"version":1,"eventDate":"2026-10-26","sections":[]}')
    repository = LocationRepository(path, schedule_path)
    created = repository.create("Auditório")
    assert created == {"id": "loc-003", "name": "Auditório"}
    assert read_json(path)["nextId"] == 4


def test_atomic_write_keeps_original_when_replace_fails(tmp_path, monkeypatch):
    path = tmp_path / "data.json"
    path.write_text('{"value":"original"}', encoding="utf-8")
    monkeypatch.setattr(os, "replace", Mock(side_effect=OSError("falha")))
    with pytest.raises(OSError):
        atomic_write_json(path, {"value": "novo"})
    assert read_json(path) == {"value": "original"}
```

Add tests for duplicate names, deletion while in use, exact name propagation, and axis renaming without changing the ID.

- [ ] **Step 2: run and confirm failures**

Run: `uv run pytest tests/test_json_clients.py -v`

Expected: failure because the clients do not exist yet.

- [ ] **Step 3: implement atomic writes**

```python
def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
```


- [ ] **Step 4: implement repositories and cross-file consistency**

`LocationRepository.__init__(path: Path, schedule_path: Path)`, `list() -> list[dict]`, `create(name: str) -> dict`, `rename(location_id: str, name: str) -> dict`, and `delete(location_id: str) -> None` comprise the catalog interface. `rename` validates both documents before writing, saves in-memory copies, writes the catalog, writes the propagated schedule, and restores the catalog if the second write fails. `delete` collects the titles of activities that use the name and raises `ResourceInUseError(references: list[str])`.

`KnowledgeAxisRepository.__init__(path: Path, schedule_path: Path)` exposes the same five methods. It keeps the ID stable after creation, rejects deletion while in use, and generates a Portuguese slug with `-2`, `-3` suffixes on collisions.

At call time, the path functions read `SCHEDULE_PATH`, `LOCATIONS_PATH`, and `KNOWLEDGE_AXES_PATH`, defaulting to the files under `db/`. This lets routes and tests use the same repositories without touching real data.

- [ ] **Step 5: generate the initial catalogs and migrate axes**

Create `locations.json` with `nextId` and every current unique name, alphabetically sorted. Create `knowledge_axes.json` with the ten Portuguese IDs specified in the design. Replace all ten English references in `schedule.json` with the Portuguese IDs; leave groups without `knowledgeAxis` unchanged.

- [ ] **Step 6: verify data and tests**

```powershell
uv run pytest tests/test_json_clients.py tests/test_schedule_models.py -v
uv run python -m json.tool db/locations.json > $null
uv run python -m json.tool db/knowledge_axes.json > $null
uv run python -m json.tool db/schedule.json > $null
uv run ruff check clients models tests
uv run ty check
```

- [ ] **Step 7: commit**

```powershell
git add clients/json_store.py clients/schedule.py clients/locations.py clients/knowledge_axes.py db tests/test_json_clients.py
git commit -m "Adiciona persistência da agenda e catálogos"
```

---

### Task 3: Authenticated administrative APIs

**Files:**
- Create: `backend/routes/schedule.py`
- Create: `backend/routes/locations.py`
- Create: `backend/routes/knowledge_axes.py`
- Create: `backend/tests/test_admin_api.py`

**Interfaces:**
- Consumes: repositories from Task 2 and `CurrentTokenData` from `dependencies.py`.
- Produces: endpoints at `/admin/api/schedule`, `/admin/api/locations`, and `/admin/api/knowledge-axes`.

- [ ] **Step 1: write authentication and HTTP contract tests**

```python
def test_schedule_requires_authentication(client):
    response = client.get("/admin/api/schedule")
    assert response.status_code == 401


def test_create_location_with_token(client, auth_headers):
    response = client.post(
        "/admin/api/locations", json={"name": "Novo auditório"}, headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Novo auditório"


def test_delete_location_in_use_returns_references(client, auth_headers):
    response = client.delete("/admin/api/locations/loc-001", headers=auth_headers)
    assert response.status_code == 409
    assert response.json()["detail"]["references"]
```

Override the dependencies that provide paths/repositories in the `client` fixture, pointing them to the temporary JSON files.

- [ ] **Step 2: run and confirm failures**

Run: `uv run pytest tests/test_admin_api.py -v`

Expected: `404` because the routers are not yet registered in the test app.

- [ ] **Step 3: implement input models and thin handlers**

```python
router = APIRouter(prefix="/admin/api/locations", tags=["admin-locations"])


class LocationInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)


def get_location_repository() -> LocationRepository:
    return LocationRepository(get_locations_path(), get_schedule_path())


LocationRepo = Annotated[LocationRepository, Depends(get_location_repository)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_location(payload: LocationInput, _: CurrentTokenData, repository: LocationRepo):
    return repository.create(payload.name.strip())
```

Map `ResourceInUseError` and duplicates to `409`, missing resources to `404`, and let Pydantic produce `422`. `PUT /schedule` accepts `ScheduleDocument` and serializes it with `model_dump(by_alias=True, mode="json", exclude_none=True)`.

- [ ] **Step 4: run the API suite and static checks**

```powershell
uv run pytest tests/test_admin_api.py -v
uv run ruff check routes tests/test_admin_api.py
uv run ty check
```

- [ ] **Step 5: commit**

```powershell
git add routes/schedule.py routes/locations.py routes/knowledge_axes.py tests/test_admin_api.py tests/conftest.py
git commit -m "Adiciona APIs administrativas autenticadas"
```

---

### Task 4: Administrative page and authentication flow

**Files:**
- Create: `backend/routes/admin.py`
- Create: `backend/static/admin/index.html`
- Create: `backend/static/admin/admin.css`
- Create: `backend/static/admin/admin.js`
- Modify: `backend/clients/db.py`
- Modify: `backend/app.py`
- Create: `backend/tests/test_admin_page.py`

**Interfaces:**
- Consumes: `/auth/token`, `/auth/users/me/`, and the Task 3 APIs.
- Produces: `/admin`, `/admin/static/admin.css`, `/admin/static/admin.js`, and the JS functions `apiFetch`, `showLogin`, `showEditor`, `loadAdminData`, `logout`.

- [ ] **Step 1: write the page and static mounting test**

```python
def test_admin_page_is_served_without_embedding_schedule(client):
    response = client.get("/admin")
    assert response.status_code == 200
    assert 'id="login-view"' in response.text
    assert "Programação completa" not in response.text


def test_admin_javascript_is_served(client):
    response = client.get("/admin/static/admin.js")
    assert response.status_code == 200
    assert "sessionStorage" in response.text
```

- [ ] **Step 2: confirm failures**

Run: `uv run pytest tests/test_admin_page.py -v`

Expected: `404` for the page and JavaScript.

- [ ] **Step 3: create HTML without administrative data and responsive CSS**

The HTML contains `#login-view`, `#editor-view`, a login form, `Programação`/`Locais`/`Eixos`/`Minha conta` navigation, `aria-live` regions, an accessible modal, and `<template>` templates for groups, activities, and sessions. The CSS implements the approved side navigation and collapses to top navigation below 750 px.

- [ ] **Step 4: make the user database configurable for isolated tests**

```python
def get_database_path() -> Path:
    return Path(os.environ.get("DATABASE_PATH", "db/users.json"))


def load_database(db_path: str | Path | None = None) -> dict:
    path = Path(db_path) if db_path is not None else get_database_path()
    with path.open("r", encoding="utf-8") as database_file:
        return json.load(database_file)
```

Remove default arguments bound to `DATABASE_PATH` at import time; `get_user` and `database_connection` accept `None` and resolve the path inside the function. Keep `DATABASE_PATH` exported for compatibility with `dependencies.py`.

- [ ] **Step 5: implement browser authentication**

```javascript
async function apiFetch(path, options = {}) {
  const token = sessionStorage.getItem("adminToken");
  const headers = new Headers(options.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(path, {...options, headers});
  if (response.status === 401) {
    sessionStorage.removeItem("adminToken");
    showLogin("Sua sessão expirou. Entre novamente.");
    throw new Error("unauthorized");
  }
  return response;
}
```

Login submission uses `URLSearchParams` for `/auth/token`, stores only `access_token` in `sessionStorage`, validates `/auth/users/me/`, and then calls `loadAdminData()`.

- [ ] **Step 6: register routes while preserving existing changes**

In `app.py`, import the four new routers, mount `StaticFiles(directory=ADMIN_STATIC_DIR)` at `/admin/static`, and call `include_router` for each router. Do not reformat or overwrite sections modified by the user.

- [ ] **Step 7: run tests and lint**

```powershell
uv run pytest tests/test_admin_page.py tests/test_admin_api.py -v
uv run ruff check app.py routes
uv run ty check
```

- [ ] **Step 8: commit**

```powershell
git add app.py clients/db.py routes/admin.py static/admin tests/test_admin_page.py
git commit -m "Serve painel administrativo autenticado"
```

---

### Task 5: User-friendly schedule editor

**Files:**
- Modify: `backend/static/admin/index.html`
- Modify: `backend/static/admin/admin.css`
- Modify: `backend/static/admin/admin.js`
- Create: `backend/tests/test_admin_editor_js.py`

**Interfaces:**
- Consumes: the document returned by `GET /admin/api/schedule` and API catalogs.
- Produces: JS functions `renderSections`, `renderGroups`, `openActivityEditor`, `addSession`, `validateDraft`, and `saveSchedule`.

- [ ] **Step 1: write editor contract tests**

```python
def test_editor_contains_every_required_control(client):
    html = client.get("/admin").text
    required = ["add-section", "add-group", "add-activity", "add-session", "save-schedule"]
    for control_id in required:
        assert f'id="{control_id}"' in html


def test_editor_script_uses_portuguese_error_messages(client):
    script = client.get("/admin/static/admin.js").text
    assert "O horário final deve ser posterior ao inicial" in script
    assert "Não foi possível salvar a programação" in script
```

- [ ] **Step 2: confirm failures**

Run: `uv run pytest tests/test_admin_editor_js.py -v`

- [ ] **Step 3: implement the draft and hierarchical editing**

Maintain `state = {schedule, locations, knowledgeAxes, selectedSectionId}`. Every action changes only `state.schedule` until saving. New IDs use the title slug and append `-2`, `-3` as necessary. Locations appear by `name`; axes appear by `name` and store `id` in `knowledgeAxis`.

- [ ] **Step 4: implement validation and saving**

```javascript
async function saveSchedule() {
  const errors = validateDraft(state.schedule);
  if (errors.length) return showErrors(errors);
  const response = await apiFetch("/admin/api/schedule", {
    method: "PUT",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(state.schedule),
  });
  if (!response.ok) return showApiError(response, "Não foi possível salvar a programação");
  state.schedule = await response.json();
  announce("Programação salva com sucesso.");
}
```

All visible buttons receive listeners; deletions use confirmation; after closing a modal, focus returns to the control that opened it.

- [ ] **Step 5: run tests and a short manual check**

```powershell
uv run pytest tests/test_admin_editor_js.py tests/test_admin_page.py -v
uv run uvicorn app:app --env-file .env
```

Verify at `/admin`: the keyboard reaches every control, groups expand, the modal opens/closes, times are added, and messages appear.

- [ ] **Step 6: commit**

```powershell
git add static/admin tests/test_admin_editor_js.py
git commit -m "Adiciona editor amigável da programação"
```

---

### Task 6: Location and axis screens

**Files:**
- Modify: `backend/static/admin/index.html`
- Modify: `backend/static/admin/admin.css`
- Modify: `backend/static/admin/admin.js`
- Create: `backend/tests/test_catalog_ui_contract.py`

**Interfaces:**
- Consumes: the location and axis APIs from Task 3.
- Produces: JS functions `renderLocations`, `saveLocation`, `deleteLocation`, `renderKnowledgeAxes`, `saveKnowledgeAxis`, and `deleteKnowledgeAxis`.

- [ ] **Step 1: write tests for controls and messages**

```python
def test_location_form_only_asks_for_name(client):
    html = client.get("/admin").text
    fragment = html.split('id="location-form"', 1)[1].split("</form>", 1)[0]
    assert 'name="name"' in fragment
    assert 'name="block"' not in fragment
    assert 'name="room"' not in fragment


def test_catalog_script_handles_resource_in_use(client):
    script = client.get("/admin/static/admin.js").text
    assert "Este registro ainda está em uso" in script
```

- [ ] **Step 2: confirm failures**

Run: `uv run pytest tests/test_catalog_ui_contract.py -v`

- [ ] **Step 3: implement location CRUD**

The list displays only the name and actions. The form contains only `name`; it does not show the ID. After renaming, reload the schedule and locations to reflect propagation. On `409`, list the activities returned by `detail.references`.

- [ ] **Step 4: implement axis CRUD**

The list displays the Portuguese name, number of groups, and actions. The form contains only the name. The ID is not editable; groups without an axis use the “Sem eixo” option. On `409`, show the groups that prevent deletion.

- [ ] **Step 5: run tests**

```powershell
uv run pytest tests/test_catalog_ui_contract.py tests/test_admin_editor_js.py -v
uv run ruff check tests
```

- [ ] **Step 6: commit**

```powershell
git add static/admin tests/test_catalog_ui_contract.py
git commit -m "Adiciona gestão de locais e eixos"
```

---

### Task 7: Playwright, documentation, and final verification

**Files:**
- Create: `backend/tests/e2e/conftest.py`
- Create: `backend/tests/e2e/test_admin_panel.py`
- Modify: `backend/README.md`
- Modify: `backend/ARCHITECTURE.md`

**Interfaces:**
- Consumes: the complete application from Tasks 1–6.
- Produces: a reproducible E2E suite and operational instructions.

- [ ] **Step 1: create isolated E2E fixtures**

```python
@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def admin_page(browser, live_server):
    page = browser.new_page()
    page.goto(f"{live_server}/admin")
    yield page
    page.close()
```

The `temporary_databases(tmp_path, monkeypatch)` fixture copies `users.json`, `schedule.json`, `locations.json`, and `knowledge_axes.json`, then sets `DATABASE_PATH`, `SCHEDULE_PATH`, `LOCATIONS_PATH`, and `KNOWLEDGE_AXES_PATH`. The `live_server(temporary_databases, monkeypatch)` fixture sets `TOKEN_JWT`, reserves a port with `socket.bind(("127.0.0.1", 0))`, starts `uvicorn.Server` in a `threading.Thread`, waits for `server.started`, provides the URL, and sets `server.should_exit = True` in `finally` before calling `thread.join(timeout=5)`.

- [ ] **Step 2: write Playwright flows before running them**

```python
def test_admin_can_create_location_and_use_it_in_session(admin_page):
    login(admin_page)
    admin_page.get_by_role("button", name="Locais").click()
    admin_page.get_by_role("button", name="Novo local").click()
    admin_page.get_by_label("Nome do local").fill("Auditório principal")
    admin_page.get_by_role("button", name="Aplicar").click()
    admin_page.get_by_role("button", name="Programação").click()
    admin_page.get_by_text("Voz e Ação").click()
    admin_page.get_by_label("Local").select_option(label="Auditório principal")
    admin_page.get_by_role("button", name="Aplicar").click()
    admin_page.get_by_role("button", name="Salvar alterações").click()
    expect(admin_page.get_by_text("Programação salva com sucesso.")).to_be_visible()
```

Add separate cases for invalid login, expired session, axis creation, blocking deletion while in use, activity/time editing, and persistence after reloading.

- [ ] **Step 3: install Chromium and confirm useful failures**

```powershell
uv run playwright install chromium
uv run pytest tests/e2e/test_admin_panel.py -v
```

Fix only real problems revealed by the flows; do not weaken selectors or assertions to hide failures.

- [ ] **Step 4: document usage and architecture**

In the README, document installation, `uv run playwright install chromium`, startup, the `/admin` URL, and test commands. In `ARCHITECTURE.md`, document models, clients, routers, static files, catalogs, and the browser → authenticated API → JSON client flow.

- [ ] **Step 5: run complete verification**

```powershell
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
uv run ty check
```

Expected: all tests and checks pass. Also confirm that `git diff -- frontend` shows no changes.

- [ ] **Step 6: final delivery commit**

```powershell
git add tests/e2e README.md ARCHITECTURE.md
git commit -m "Testa painel administrativo no navegador"
```

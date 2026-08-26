# Painel administrativo da agenda Implementation Plan

> **Para agentes executores:** SUB-SKILL OBRIGATÓRIA: use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar este plano tarefa por tarefa. Os passos usam caixas de seleção (`- [ ]`) para acompanhamento.

**Objetivo:** Entregar em `/admin` um painel autenticado, independente do frontend público, para editar a agenda, os locais e os eixos armazenados em JSON.

**Arquitetura:** O FastAPI servirá HTML, CSS e JavaScript puro e exporá APIs administrativas protegidas por `CurrentTokenData`. Modelos Pydantic validarão a agenda; clientes focados encapsularão leitura e escrita atômica dos três JSONs. Testes de API usarão diretórios temporários e Playwright validará os fluxos reais no navegador.

**Stack técnica:** Python 3.14, FastAPI 0.141+, Pydantic, pytest, TestClient, Playwright para Python, HTML5, CSS e JavaScript sem framework.

**Especificação:** `docs/superpowers/specs/2026-08-26-painel-administrativo-agenda-design.md`

## Restrições globais

- Não modificar nem depender da pasta `frontend/`.
- Preservar o formato público de `backend/db/schedule.json`, exceto pela migração aprovada dos eixos para identificadores em português.
- Exigir JWT válido em todas as APIs de agenda, locais e eixos; o HTML estático não contém dados administrativos.
- Manter o token somente em `sessionStorage`.
- Gerar e ocultar IDs; locais aceitam somente `name` e recebem IDs `loc-NNN`.
- Considerar uma única pessoa editando por vez; não adicionar bloqueios ou versionamento.
- Gravar JSON de forma atômica e restaurar os dados anteriores se uma operação entre dois arquivos falhar.
- Usar cópias temporárias dos JSONs em todos os testes.
- Preservar alterações preexistentes do usuário em `backend/app.py`, `backend/routes/auth.py`, `backend/pyproject.toml` e `backend/uv.lock`.

---

## Estrutura de arquivos

- Criar `backend/models/schedule.py`: modelos Pydantic e validações estruturais da agenda.
- Criar `backend/clients/json_store.py`: leitura e substituição atômica reutilizável.
- Criar `backend/clients/schedule.py`: acesso à agenda e busca/propagação de referências.
- Criar `backend/clients/locations.py`: CRUD do catálogo simples de locais.
- Criar `backend/clients/knowledge_axes.py`: CRUD e migração dos eixos.
- Criar `backend/routes/admin.py`: entrega do documento HTML.
- Criar `backend/routes/schedule.py`, `locations.py` e `knowledge_axes.py`: APIs autenticadas.
- Criar `backend/static/admin/index.html`, `admin.css` e `admin.js`: painel sem build.
- Criar `backend/db/locations.json` e `knowledge_axes.json`: dados iniciais normalizados.
- Criar `backend/tests/`: testes isolados de modelos, clientes, rotas e navegador.
- Modificar `backend/clients/db.py`: resolver `DATABASE_PATH` no momento da chamada para isolar autenticação nos testes.
- Modificar `backend/app.py`: registrar roteadores e montar `/admin/static`.
- Modificar `backend/pyproject.toml` e `backend/uv.lock`: acrescentar pytest sem remover o Playwright já adicionado.
- Modificar `backend/ARCHITECTURE.md` e `backend/README.md`: documentar responsabilidades e execução.

---

### Tarefa 1: Infraestrutura de testes e modelos da agenda

**Arquivos:**
- Modificar: `backend/pyproject.toml`
- Modificar mecanicamente: `backend/uv.lock`
- Criar: `backend/models/__init__.py`
- Criar: `backend/models/schedule.py`
- Criar: `backend/tests/conftest.py`
- Criar: `backend/tests/test_schedule_models.py`

**Interfaces:**
- Consome: formato atual de `db/schedule.json`.
- Produz: `ScheduleDocument`, `Section`, `ScheduleGroup`, `Activity`, `Session` e `slugify_id(value: str) -> str`.

- [ ] **Passo 1: adicionar pytest ao grupo de desenvolvimento**

Preservar `playwright>=1.62.0` já presente e acrescentar:

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

Executar: `uv lock`

- [ ] **Passo 2: escrever testes que expressem o contrato da agenda**

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

- [ ] **Passo 3: executar os testes e confirmar a falha**

Executar: `uv run pytest tests/test_schedule_models.py -v`

Esperado: falha de importação de `models.schedule`.

- [ ] **Passo 4: implementar modelos com aliases do JSON**

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

Implementar os modelos intermediários com os campos opcionais existentes e uma validação de IDs únicos em todo o documento. `slugify_id` usa `unicodedata.normalize`, letras minúsculas, hífens e sufixo numérico quando o chamador detectar colisão.

- [ ] **Passo 5: executar testes, lint e tipos**

Executar:

```powershell
uv run pytest tests/test_schedule_models.py -v
uv run ruff check models tests/test_schedule_models.py
uv run ty check
```

Esperado: todos passam.

- [ ] **Passo 6: commit**

```powershell
git add pyproject.toml uv.lock models tests/conftest.py tests/test_schedule_models.py
git commit -m "Adiciona modelos validados da agenda"
```

---

### Tarefa 2: Persistência atômica e catálogos iniciais

**Arquivos:**
- Criar: `backend/clients/json_store.py`
- Criar: `backend/clients/schedule.py`
- Criar: `backend/clients/locations.py`
- Criar: `backend/clients/knowledge_axes.py`
- Criar: `backend/db/locations.json`
- Criar: `backend/db/knowledge_axes.json`
- Modificar: `backend/db/schedule.json`
- Criar: `backend/tests/test_json_clients.py`

**Interfaces:**
- Consome: `ScheduleDocument` e `slugify_id` da Tarefa 1.
- Produz: `read_json(path: Path) -> dict`, `atomic_write_json(path: Path, payload: dict) -> None`, `load_schedule(path: Path) -> ScheduleDocument`, `save_schedule(document: ScheduleDocument, path: Path) -> None`, `get_schedule_path() -> Path`, `get_locations_path() -> Path`, `get_knowledge_axes_path() -> Path`, `LocationRepository` e `KnowledgeAxisRepository`.

- [ ] **Passo 1: escrever testes de gravação e CRUD isolados**

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

Adicionar testes para nomes duplicados, exclusão em uso, propagação exata de nome e renomeação de eixo sem alterar o ID.

- [ ] **Passo 2: executar e confirmar falhas**

Executar: `uv run pytest tests/test_json_clients.py -v`

Esperado: falha porque os clientes ainda não existem.

- [ ] **Passo 3: implementar escrita atômica**

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

- [ ] **Passo 4: implementar repositórios e consistência entre arquivos**

`LocationRepository.__init__(path: Path, schedule_path: Path)`, `list() -> list[dict]`, `create(name: str) -> dict`, `rename(location_id: str, name: str) -> dict` e `delete(location_id: str) -> None` formam a interface do catálogo. `rename` valida ambos os documentos antes da escrita, salva cópias em memória, grava o catálogo, grava a agenda propagada e restaura o catálogo se a segunda gravação falhar. `delete` coleta títulos das atividades que usam o nome e levanta `ResourceInUseError(references: list[str])`.

`KnowledgeAxisRepository.__init__(path: Path, schedule_path: Path)` expõe os mesmos cinco métodos. Ele mantém o ID estável após criação, recusa exclusão em uso e gera slug em português com sufixos `-2`, `-3` em colisões.

As funções de caminho leem, no momento da chamada, `SCHEDULE_PATH`, `LOCATIONS_PATH` e `KNOWLEDGE_AXES_PATH`, usando os arquivos de `db/` como padrão. Isso permite que rotas e testes usem os mesmos repositórios sem tocar nos dados reais.

- [ ] **Passo 5: gerar os catálogos iniciais e migrar eixos**

Criar `locations.json` com `nextId` e todos os nomes únicos atuais, ordenados alfabeticamente. Criar `knowledge_axes.json` com os dez IDs em português especificados no design. Substituir em `schedule.json` todas as dez referências inglesas pelos IDs portugueses; manter grupos sem `knowledgeAxis` inalterados.

- [ ] **Passo 6: verificar os dados e testes**

```powershell
uv run pytest tests/test_json_clients.py tests/test_schedule_models.py -v
uv run python -m json.tool db/locations.json > $null
uv run python -m json.tool db/knowledge_axes.json > $null
uv run python -m json.tool db/schedule.json > $null
uv run ruff check clients models tests
uv run ty check
```

- [ ] **Passo 7: commit**

```powershell
git add clients/json_store.py clients/schedule.py clients/locations.py clients/knowledge_axes.py db tests/test_json_clients.py
git commit -m "Adiciona persistência da agenda e catálogos"
```

---

### Tarefa 3: APIs administrativas autenticadas

**Arquivos:**
- Criar: `backend/routes/schedule.py`
- Criar: `backend/routes/locations.py`
- Criar: `backend/routes/knowledge_axes.py`
- Criar: `backend/tests/test_admin_api.py`

**Interfaces:**
- Consome: repositórios da Tarefa 2 e `CurrentTokenData` de `dependencies.py`.
- Produz: endpoints em `/admin/api/schedule`, `/admin/api/locations` e `/admin/api/knowledge-axes`.

- [ ] **Passo 1: escrever testes de autenticação e contratos HTTP**

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

Sobrescrever as dependências que fornecem caminhos/repositórios no fixture `client`, apontando para os JSONs temporários.

- [ ] **Passo 2: executar e confirmar falhas**

Executar: `uv run pytest tests/test_admin_api.py -v`

Esperado: `404` porque os roteadores ainda não foram registrados no app de teste.

- [ ] **Passo 3: implementar modelos de entrada e handlers finos**

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

Mapear `ResourceInUseError` e duplicidade para `409`, ausentes para `404` e deixar Pydantic produzir `422`. O `PUT /schedule` recebe `ScheduleDocument` e serializa com `model_dump(by_alias=True, mode="json", exclude_none=True)`.

- [ ] **Passo 4: executar suíte de API e verificações estáticas**

```powershell
uv run pytest tests/test_admin_api.py -v
uv run ruff check routes tests/test_admin_api.py
uv run ty check
```

- [ ] **Passo 5: commit**

```powershell
git add routes/schedule.py routes/locations.py routes/knowledge_axes.py tests/test_admin_api.py tests/conftest.py
git commit -m "Adiciona APIs administrativas autenticadas"
```

---

### Tarefa 4: Página administrativa e fluxo de autenticação

**Arquivos:**
- Criar: `backend/routes/admin.py`
- Criar: `backend/static/admin/index.html`
- Criar: `backend/static/admin/admin.css`
- Criar: `backend/static/admin/admin.js`
- Modificar: `backend/clients/db.py`
- Modificar: `backend/app.py`
- Criar: `backend/tests/test_admin_page.py`

**Interfaces:**
- Consome: `/auth/token`, `/auth/users/me/` e APIs da Tarefa 3.
- Produz: `/admin`, `/admin/static/admin.css`, `/admin/static/admin.js` e funções JS `apiFetch`, `showLogin`, `showEditor`, `loadAdminData`, `logout`.

- [ ] **Passo 1: escrever teste da página e montagem estática**

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

- [ ] **Passo 2: confirmar falhas**

Executar: `uv run pytest tests/test_admin_page.py -v`

Esperado: `404` para a página e o JavaScript.

- [ ] **Passo 3: criar HTML sem dados administrativos e CSS responsivo**

O HTML contém `#login-view`, `#editor-view`, formulário de login, navegação Programação/Locais/Eixos/Minha conta, regiões `aria-live`, modal acessível e templates `<template>` para grupos, atividades e sessões. O CSS implementa a navegação lateral aprovada e colapsa para navegação superior abaixo de 750 px.

- [ ] **Passo 4: tornar o banco de usuários configurável para testes isolados**

```python
def get_database_path() -> Path:
    return Path(os.environ.get("DATABASE_PATH", "db/users.json"))


def load_database(db_path: str | Path | None = None) -> dict:
    path = Path(db_path) if db_path is not None else get_database_path()
    with path.open("r", encoding="utf-8") as database_file:
        return json.load(database_file)
```

Remover argumentos padrão vinculados a `DATABASE_PATH` na importação; `get_user` e `database_connection` aceitam `None` e resolvem o caminho dentro da função. Manter `DATABASE_PATH` exportado para compatibilidade com `dependencies.py`.

- [ ] **Passo 5: implementar autenticação no navegador**

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

O submit do login usa `URLSearchParams` para `/auth/token`, guarda apenas `access_token` em `sessionStorage`, valida `/auth/users/me/` e então chama `loadAdminData()`.

- [ ] **Passo 6: registrar rotas preservando mudanças existentes**

Em `app.py`, importar os quatro novos roteadores, montar `StaticFiles(directory=ADMIN_STATIC_DIR)` em `/admin/static` e chamar `include_router` para cada roteador. Não reformatar nem sobrescrever trechos modificados pelo usuário.

- [ ] **Passo 7: executar testes e lint**

```powershell
uv run pytest tests/test_admin_page.py tests/test_admin_api.py -v
uv run ruff check app.py routes
uv run ty check
```

- [ ] **Passo 8: commit**

```powershell
git add app.py clients/db.py routes/admin.py static/admin tests/test_admin_page.py
git commit -m "Serve painel administrativo autenticado"
```

---

### Tarefa 5: Editor amigável da programação

**Arquivos:**
- Modificar: `backend/static/admin/index.html`
- Modificar: `backend/static/admin/admin.css`
- Modificar: `backend/static/admin/admin.js`
- Criar: `backend/tests/test_admin_editor_js.py`

**Interfaces:**
- Consome: documento retornado por `GET /admin/api/schedule` e catálogos das APIs.
- Produz: funções JS `renderSections`, `renderGroups`, `openActivityEditor`, `addSession`, `validateDraft` e `saveSchedule`.

- [ ] **Passo 1: escrever testes de contrato do editor**

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

- [ ] **Passo 2: confirmar falhas**

Executar: `uv run pytest tests/test_admin_editor_js.py -v`

- [ ] **Passo 3: implementar o rascunho e edição hierárquica**

Manter `state = {schedule, locations, knowledgeAxes, selectedSectionId}`. Toda ação altera somente `state.schedule` até salvar. Novos IDs usam o slug do título e acrescentam `-2`, `-3` quando necessário. Locais aparecem por `name`; eixos aparecem por `name` e gravam `id` em `knowledgeAxis`.

- [ ] **Passo 4: implementar validação e salvamento**

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

Todos os botões visíveis recebem listeners; exclusões usam confirmação; após fechar modal, o foco retorna ao controle que o abriu.

- [ ] **Passo 5: executar testes e verificação manual curta**

```powershell
uv run pytest tests/test_admin_editor_js.py tests/test_admin_page.py -v
uv run uvicorn app:app --env-file .env
```

Verificar em `/admin`: teclado alcança todos os controles, grupos expandem, modal abre/fecha, horários são adicionados e mensagens aparecem.

- [ ] **Passo 6: commit**

```powershell
git add static/admin tests/test_admin_editor_js.py
git commit -m "Adiciona editor amigável da programação"
```

---

### Tarefa 6: Telas de locais e eixos

**Arquivos:**
- Modificar: `backend/static/admin/index.html`
- Modificar: `backend/static/admin/admin.css`
- Modificar: `backend/static/admin/admin.js`
- Criar: `backend/tests/test_catalog_ui_contract.py`

**Interfaces:**
- Consome: APIs de locais e eixos da Tarefa 3.
- Produz: funções JS `renderLocations`, `saveLocation`, `deleteLocation`, `renderKnowledgeAxes`, `saveKnowledgeAxis`, `deleteKnowledgeAxis`.

- [ ] **Passo 1: escrever testes dos controles e mensagens**

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

- [ ] **Passo 2: confirmar falhas**

Executar: `uv run pytest tests/test_catalog_ui_contract.py -v`

- [ ] **Passo 3: implementar CRUD de locais**

A lista exibe somente o nome e ações. O formulário contém somente `name`; não mostra ID. Após renomear, recarrega agenda e locais para refletir a propagação. Em `409`, lista as atividades retornadas por `detail.references`.

- [ ] **Passo 4: implementar CRUD de eixos**

A lista exibe o nome português, quantidade de grupos e ações. O formulário contém somente o nome. O ID não é editável; grupos sem eixo usam a opção “Sem eixo”. Em `409`, mostrar os grupos que impedem a exclusão.

- [ ] **Passo 5: executar testes**

```powershell
uv run pytest tests/test_catalog_ui_contract.py tests/test_admin_editor_js.py -v
uv run ruff check tests
```

- [ ] **Passo 6: commit**

```powershell
git add static/admin tests/test_catalog_ui_contract.py
git commit -m "Adiciona gestão de locais e eixos"
```

---

### Tarefa 7: Playwright, documentação e verificação final

**Arquivos:**
- Criar: `backend/tests/e2e/conftest.py`
- Criar: `backend/tests/e2e/test_admin_panel.py`
- Modificar: `backend/README.md`
- Modificar: `backend/ARCHITECTURE.md`

**Interfaces:**
- Consome: aplicação completa das Tarefas 1–6.
- Produz: suíte E2E reproduzível e instruções operacionais.

- [ ] **Passo 1: criar fixtures E2E isoladas**

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

O fixture `temporary_databases(tmp_path, monkeypatch)` copia `users.json`, `schedule.json`, `locations.json` e `knowledge_axes.json`, depois define `DATABASE_PATH`, `SCHEDULE_PATH`, `LOCATIONS_PATH` e `KNOWLEDGE_AXES_PATH`. O fixture `live_server(temporary_databases, monkeypatch)` define `TOKEN_JWT`, reserva uma porta com `socket.bind(("127.0.0.1", 0))`, inicia `uvicorn.Server` em uma `threading.Thread`, espera `server.started`, fornece a URL e define `server.should_exit = True` no `finally` antes de chamar `thread.join(timeout=5)`.

- [ ] **Passo 2: escrever fluxos Playwright antes de executá-los**

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

Adicionar casos separados para login inválido, sessão expirada, criação de eixo, bloqueio de exclusão em uso, edição de atividade/horário e persistência após recarregar.

- [ ] **Passo 3: instalar Chromium e confirmar falhas úteis**

```powershell
uv run playwright install chromium
uv run pytest tests/e2e/test_admin_panel.py -v
```

Corrigir somente problemas reais revelados pelos fluxos; não enfraquecer seletores ou asserções para ocultar falhas.

- [ ] **Passo 4: documentar uso e arquitetura**

No README, registrar instalação, `uv run playwright install chromium`, inicialização, URL `/admin` e comandos de teste. Em `ARCHITECTURE.md`, registrar modelos, clientes, roteadores, arquivos estáticos, catálogos e o fluxo navegador → API autenticada → cliente JSON.

- [ ] **Passo 5: executar verificação completa**

```powershell
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
uv run ty check
```

Esperado: todos os testes e verificações passam. Confirmar também que `git diff -- frontend` não mostra alterações.

- [ ] **Passo 6: commit final da entrega**

```powershell
git add tests/e2e README.md ARCHITECTURE.md
git commit -m "Testa painel administrativo no navegador"
```

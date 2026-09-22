# Site público orientado por JSON Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer o site público renderizar a programação e os estados temporais exclusivamente dos JSONs do backend, mantendo `eventDate` em `settings.json` e preservando a fronteira de edição autenticada do painel.

**Architecture:** O backend terá um documento e client próprios para configurações, uma API autenticada `/api/settings` e uma rota pública read-only `/db/{file_name}` limitada aos quatro documentos públicos. O site receberá apenas um shell HTML; `schedule.js` carregará os quatro JSONs, normalizará os catálogos, derivará as visões e montará a agenda e o carrossel. O painel continuará usando `/api/*`, salvando a agenda e as configurações em operações separadas.

**Tech Stack:** Python 3.14, FastAPI, Pydantic, persistência JSON atômica existente, JavaScript sem bundler, HTML/CSS, pytest e Playwright.

**Spec:** `docs/superpowers/specs/2026-09-22-site-publico-agenda-json-design.md`

## Global Constraints

- `GET /db/{file_name}` publicará somente `schedule.json`, `knowledge_axes.json`, `locations.json` e `settings.json`.
- Os factories de caminho `SCHEDULE_PATH`, `LOCATIONS_PATH`, `KNOWLEDGE_AXES_PATH` e `SETTINGS_PATH` serão resolvidos no momento de cada chamada.
- `schedule.json` conterá somente `version` e `sections`; `eventDate` existirá exclusivamente em `settings.json`.
- A data configurada será combinada com `America/Sao_Paulo`, e cada atividade exibirá o texto `AO VIVO`, `EM BREVE` ou `FINALIZADA`.
- O site público fará somente `GET` aos quatro JSONs e não chamará nem escreverá em `/api/*`.
- O HTML público não conterá títulos, descrições, horários, locais, eixos, datas, IDs ou cards persistidos da agenda.
- Handlers permanecerão finos; validação, leitura e gravação ficarão nos modelos e clients apropriados.
- JSON continuará sendo salvo atomicamente com arquivo temporário, `fsync` e `os.replace`; falhas de filesystem serão convertidas em `PersistenceError`.
- O frontend continuará build-free, sem `package.json`, bundler ou dependência de runtime.
- A identidade pública, os assets do hero, os tokens semânticos, o foco visível, a responsividade e `prefers-reduced-motion` serão preservados conforme `static/site/DESIGN.md`.
- `static/admin/DESIGN.md` não será alterado; o painel continuará autenticado e separado do site público.
- Serão usados `uv`, quatro espaços, type hints públicos e limite de 100 caracteres configurado no Ruff.

## Review Focus

- Nome de arquivo fora da allowlist, tentativa de traversal, arquivo ausente ou irregular: a rota deve responder sem expor caminho local, segredo ou arquivo não permitido.
- Data inválida, mudança de dia e limites exatos de início/fim no fuso `America/Sao_Paulo`: a API deve rejeitar o documento inválido e o frontend deve derivar o rótulo correto a partir de um `now` determinístico.
- Grupo com eixo `null` ou desconhecido, local desconhecido, múltiplos locais e texto com marcação: o grupo deve permanecer visível, os nomes devem ser unidos com ` · ` e o DOM deve tratar o conteúdo como texto.
- Atividade com várias sessões, sessões que cruzam exatamente os limites dos turnos e IDs repetidos no conjunto do carrossel: a atividade deve aparecer nos turnos corretos, uma única vez e no máximo cinco cards.
- Falha de rede/JSON e inicialização repetida depois que o shell foi montado: a página deve manter hero, regulamento e mapa, encerrar `aria-busy`, não chamar `/api` e não duplicar listeners, clones ou cards.

## Mapa de arquivos

Arquivos novos:

- `models/settings.py` — contrato Pydantic de `settings.json`.
- `clients/settings.py` — caminho configurável, leitura e persistência atômica das configurações.
- `routes/settings.py` — fronteira autenticada `GET`/`PUT /api/settings`.
- `db/settings.json` — configuração canônica inicial com `eventDate`.
- `tests/test_settings_api.py` — contrato de modelo, client e API de configurações.
- `tests/site/test_schedule_js.py` — testes Node das funções puras de normalização, derivação e carregamento.

Arquivos existentes a modificar:

- `models/schedule.py`, `db/schedule.json` — remover `eventDate` do documento canônico.
- `routes/site.py`, `app.py` — entregar os quatro JSONs públicos com allowlist e sem schema administrativo.
- `static/admin/home.js` — carregar e salvar configurações separadamente da agenda.
- `static/site/js/schedule.js` — substituir dados codificados pela leitura, derivação e renderização dos JSONs.
- `static/site/js/carousel.js` — expor inicialização idempotente para cards montados depois do carregamento.
- `static/site/index.html` — reduzir a agenda e o carrossel a shells vazios.
- `static/site/css/main.css`, `static/site/css/schedule.css` — aplicar os estados dinâmicos sem criar tokens paralelos.
- `tests/conftest.py`, `tests/e2e/conftest.py` — copiar e configurar `settings.json` nas bases isoladas.
- `tests/test_schedule_models.py`, `tests/test_json_clients.py`, `tests/test_home_api.py`, `tests/test_routing_contract.py`, `tests/test_public_site.py`, `tests/test_home_page.py` — atualizar o contrato sem `eventDate` na agenda e cobrir a entrega pública.
- `tests/test_home_editor_js.py`, `tests/e2e/test_home_panel.py` — provar que o painel usa `/api/settings` separadamente.
- `tests/site/browser_support.py`, `tests/site/test_identity_hero.py`, `tests/site/test_carousel.py` — servir/interceptar os JSONs e validar sucesso, falha, responsividade e interação.
- `static/site/DESIGN.md`, `ARCHITECTURE.md`, `README.md` — documentar fonte de verdade, fronteira read-only e simulação temporal.

## Plano de execução

### Task 1: Criar o documento e o client de configurações

**Files:**
- Create: `models/settings.py`
- Create: `clients/settings.py`
- Create: `db/settings.json`
- Modify: `tests/conftest.py`
- Create: `tests/test_settings_api.py`

**Interfaces:**
- Consumes: `clients.json_store.read_json`, `atomic_write_json` e `PersistenceError`.
- Produces: `SettingsDocument`, `get_settings_path()`, `load_settings(path)`, `save_settings(document, path)` e `replace_settings(document, path=None)`.

- [ ] **Step 1: Escrever os testes vermelhos do contrato de configurações**

Adicionar em `tests/test_settings_api.py` os casos abaixo, usando `tmp_path` e `monkeypatch`:

```python
def test_settings_document_uses_event_date_alias_and_serializes_iso_date():
    document = SettingsDocument.model_validate({"eventDate": "2026-10-26"})

    assert document.event_date.isoformat() == "2026-10-26"
    assert document.model_dump(by_alias=True, mode="json") == {"eventDate": "2026-10-26"}


def test_settings_path_is_resolved_at_call_time(tmp_path, monkeypatch):
    first = tmp_path / "first-settings.json"
    second = tmp_path / "second-settings.json"
    monkeypatch.setenv("SETTINGS_PATH", str(first))
    assert get_settings_path() == first
    monkeypatch.setenv("SETTINGS_PATH", str(second))
    assert get_settings_path() == second


def test_replace_settings_persists_only_the_canonical_document(tmp_path):
    path = tmp_path / "settings.json"
    document = SettingsDocument.model_validate({"eventDate": "2026-09-22"})

    assert replace_settings(document, path) == document
    assert json.loads(path.read_text(encoding="utf-8")) == {"eventDate": "2026-09-22"}
```

Também cobrir `eventDate` inválido com `pytest.raises(ValidationError)` e converter uma falha de `os.replace` em `PersistenceError`, mantendo o arquivo anterior intacto.

- [ ] **Step 2: Executar os testes para confirmar a falha**

Executar:

```powershell
uv run pytest tests/test_settings_api.py -q
```

Esperado: falha porque `models.settings` e `clients.settings` ainda não existem.

- [ ] **Step 3: Implementar o modelo mínimo**

Criar `models/settings.py` com a mesma política de aliases do modelo da agenda:

```python
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class SettingsDocument(BaseModel):
    event_date: date = Field(alias="eventDate")

    model_config = ConfigDict(populate_by_name=True)
```

- [ ] **Step 4: Implementar o client com caminho tardio e persistência atômica**

Criar `clients/settings.py`. O default deve ser `db/settings.json` relativo ao backend, nunca ao cwd:

```python
def get_settings_path() -> Path:
    override = os.environ.get("SETTINGS_PATH")
    return Path(override) if override else _BACKEND_ROOT / "db" / "settings.json"


def load_settings(path: Path) -> SettingsDocument:
    return SettingsDocument.model_validate(read_json(path))


def save_settings(document: SettingsDocument, path: Path) -> None:
    atomic_write_json(
        path,
        document.model_dump(by_alias=True, exclude_unset=True, mode="json"),
    )


def replace_settings(document: SettingsDocument, path: Path | None = None) -> SettingsDocument:
    destination = path or get_settings_path()
    try:
        save_settings(document, destination)
    except OSError as error:
        raise PersistenceError("Não foi possível persistir as configurações") from error
    return document
```

- [ ] **Step 5: Criar a configuração canônica e ampliar as bases temporárias**

Criar `db/settings.json` com exatamente:

```json
{
  "eventDate": "2026-10-26"
}
```

Adicionar `settings: Path` a `TemporaryDatabase` em `tests/conftest.py`, copiar `db/settings.json` na fixture e definir `SETTINGS_PATH` em `configured_environment`. Atualizar a fixture `schedule_copy` somente se necessário para o novo documento sem `eventDate`.

- [ ] **Step 6: Executar os testes da tarefa**

Executar:

```powershell
uv run pytest tests/test_settings_api.py -q
uv run ruff check models/settings.py clients/settings.py tests/test_settings_api.py
```

Esperado: todos os casos do modelo/client passam e o caminho alternado continua sendo observado na chamada.

- [ ] **Step 7: Fazer commit**

```powershell
git add models/settings.py clients/settings.py db/settings.json tests/conftest.py tests/test_settings_api.py
git commit -m "Adiciona configurações do evento"
```

### Task 2: Separar o contrato da agenda, a API de configurações e o painel

**Files:**
- Modify: `models/schedule.py`
- Modify: `db/schedule.json`
- Create: `routes/settings.py`
- Modify: `app.py`
- Modify: `routes/schedule.py` only if imports or response typing need adjustment
- Modify: `static/admin/home.js`
- Modify: `tests/test_schedule_models.py`, `tests/test_json_clients.py`, `tests/test_home_api.py`, `tests/test_home_editor_js.py`
- Modify: `tests/e2e/conftest.py`, `tests/e2e/test_home_panel.py`

**Interfaces:**
- Consumes: `SettingsDocument` e `clients.settings` da Task 1.
- Produces: `GET /api/settings`, `PUT /api/settings`, agenda sem `eventDate` e estado administrativo `state.settings`.

- [ ] **Step 1: Atualizar testes e fixtures para o novo contrato da agenda**

Em `tests/test_schedule_models.py`, `tests/test_json_clients.py` e `tests/test_home_api.py`, remover `eventDate` de todos os payloads de `ScheduleDocument` e substituir as asserções por:

```python
document = ScheduleDocument.model_validate(
    {"version": 1, "sections": [{"id": "s", "title": "S", "groups": []}]}
)

assert "eventDate" not in document.model_dump(by_alias=True, mode="json")
```

Em `canonical_schedule()` e nos fixtures E2E, manter `version` e `sections`, sem mover a data para dentro da agenda. Adicionar a cópia de `settings.json` em `tests/e2e/conftest.py` e exportar `SETTINGS_PATH` junto aos demais caminhos.

- [ ] **Step 2: Executar a suíte de contrato para confirmar a falha**

Executar:

```powershell
uv run pytest tests/test_schedule_models.py tests/test_json_clients.py tests/test_home_api.py -q
```

Esperado: falhas nas referências antigas a `event_date`/`eventDate` e na ausência da API de configurações.

- [ ] **Step 3: Remover `event_date` do modelo e do JSON canônico**

Em `models/schedule.py`, retirar o campo `event_date` de `ScheduleDocument` e preservar `version`, `sections`, aliases, geração de IDs e todas as validações existentes. Remover a chave `eventDate` de `db/schedule.json` sem reformatar ou alterar o conteúdo das seções.

- [ ] **Step 4: Criar a rota autenticada de configurações**

Criar `routes/settings.py` seguindo o tratamento não vazante de `routes/schedule.py`:

```python
@router.get("", response_model=SettingsDocument, response_model_exclude_none=True)
def read_settings(_: CurrentTokenData, path: SettingsPath) -> dict:
    try:
        document = load_settings(path)
    except (OSError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Não foi possível carregar as configurações", "references": []},
        ) from error
    return document.model_dump(by_alias=True, mode="json", exclude_none=True)


@router.put("", response_model=SettingsDocument, response_model_exclude_none=True)
def update_settings(
    payload: SettingsDocument,
    _: CurrentTokenData,
    path: SettingsPath,
    replace: SettingsReplacer,
) -> dict:
    try:
        document = replace(payload, path)
    except PersistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Não foi possível salvar as configurações", "references": []},
        ) from error
    return document.model_dump(by_alias=True, mode="json", exclude_none=True)
```

Os aliases de dependência devem chamar `get_settings_path()` e `replace_settings()` em tempo de requisição. Registrar o router em `app.py` sob `API_PREFIX`.

- [ ] **Step 5: Adicionar testes da API e da autorização**

Em `tests/test_settings_api.py` ou `tests/test_home_api.py`, cobrir:

```python
def test_settings_routes_require_authentication(client):
    assert client.get("/api/settings").status_code == 401
    assert client.put("/api/settings", json={"eventDate": "2026-09-22"}).status_code == 401


def test_settings_api_persists_and_returns_iso_date(client, auth_headers, temporary_database):
    response = client.put(
        "/api/settings",
        json={"eventDate": "2026-09-22"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == {"eventDate": "2026-09-22"}
    assert json.loads(temporary_database.settings.read_text(encoding="utf-8")) == response.json()


def test_schedule_api_never_returns_event_date(client, auth_headers):
    response = client.get("/api/schedule", headers=auth_headers)

    assert response.status_code == 200
    assert "eventDate" not in response.json()
```

Também testar `0000-01-01`, `2026-02-30` e JSON ausente/malformado como 422 ou 500 estruturado, conforme a fronteira exercitada, sem caminho local na resposta.

- [ ] **Step 6: Separar o estado e o salvamento no painel**

Em `static/admin/home.js`:

1. Adicionar `state.settings`, `savedSettingsSnapshot()`, `settingsIsDirty()` e um validador que aceite somente uma data ISO válida.
2. Incluir `apiFetch("/settings")` em `loadAdminData()` e validar o payload com `isCanonicalSettings` antes de exibir o editor.
3. Fazer `renderSettings()` ler `state.schedule.version` para “Edição do evento” e `state.settings.eventDate` para “Data do evento”.
4. Trocar `data-action="save-schedule"` da tela de configurações por `data-action="save-settings"`.
5. Implementar `saveSettings()` com `PUT /api/settings`, corpo `JSON.stringify(state.settings)`, adoção da resposta canônica e mensagem segura de sucesso/erro.
6. Remover a validação de `eventDate` de `validateDraft()` e manter nela somente o contrato de `schedule.json`.
7. Fazer o listener `change` atualizar versão na agenda e data em `state.settings`, sem misturar os snapshots; o aviso de saída deve considerar qualquer uma das duas alterações.

O corpo enviado por `saveSchedule()` deve ser o documento de agenda sem `eventDate`; a tela de configurações nunca deve disparar `PUT /api/schedule`.

- [ ] **Step 7: Cobrir o comportamento do editor com testes Node e E2E**

Atualizar `tests/test_home_editor_js.py` para que `validSchedule()` não tenha data e adicionar um caso de configurações:

```javascript
api.state.schedule = {version: 1, sections: []};
api.state.settings = {eventDate: "2026-10-26"};
api.state.locations = [];
api.state.knowledgeAxes = [];
let sent;
context.fetch = async (path, options) => {
  sent = {path, options, body: JSON.parse(options.body)};
  return {ok: true, status: 200, json: async () => ({eventDate: "2026-09-22"})};
};

api.state.settings.eventDate = "2026-09-22";
await api.saveSettings();

assert.equal(sent.path, "/api/settings");
assert.equal(sent.options.method, "PUT");
assert.deepEqual(sent.body, {eventDate: "2026-09-22"});
assert.equal(api.state.schedule.eventDate, undefined);
```

Em `tests/e2e/test_home_panel.py`, adaptar o caso da data inválida para verificar que nenhum `PUT` para `/schedule` nem `/settings` ocorre, e adicionar o caso que altera a data, observa `PUT /api/settings`, recarrega o painel e confirma a persistência sem alterar o JSON da agenda.

- [ ] **Step 8: Executar os testes da tarefa**

Executar:

```powershell
uv run pytest tests/test_schedule_models.py tests/test_json_clients.py tests/test_home_api.py tests/test_home_editor_js.py -q
uv run pytest tests/e2e/test_home_panel.py -q
```

Esperado: a agenda continua editável pela API antiga, a data é editável somente por `/api/settings` e todos os payloads da agenda deixam de conter `eventDate`.

- [ ] **Step 9: Fazer commit**

```powershell
git add models/schedule.py db/schedule.json routes/settings.py app.py static/admin/home.js tests/test_schedule_models.py tests/test_json_clients.py tests/test_home_api.py tests/test_home_editor_js.py tests/e2e/conftest.py tests/e2e/test_home_panel.py
git commit -m "Separa data do evento da agenda"
```

### Task 3: Entregar os quatro JSONs públicos com allowlist

**Files:**
- Modify: `routes/site.py`
- Modify: `app.py`
- Modify: `tests/conftest.py` if a route dependency needs an explicit override
- Modify: `tests/test_routing_contract.py`, `tests/test_public_site.py`

**Interfaces:**
- Consumes: `get_schedule_path()`, `get_locations_path()`, `get_knowledge_axes_path()` e `get_settings_path()`.
- Produces: `GET /db/{file_name}` com `application/json`, `Cache-Control: no-cache` e `include_in_schema=False`.

- [ ] **Step 1: Escrever os testes vermelhos da fronteira pública**

Adicionar testes que verifiquem os quatro arquivos, autenticação ausente, allowlist, caminho tardio e ausência de vazamento:

```python
@pytest.mark.parametrize(
    "file_name",
    ["schedule.json", "knowledge_axes.json", "locations.json", "settings.json"],
)
def test_public_json_route_serves_only_the_allowlisted_documents(client, file_name):
    response = client.get(f"/db/{file_name}")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers["cache-control"] == "no-cache"


@pytest.mark.parametrize("file_name", ["users.json", "participants.json", "../users.json"])
def test_public_json_route_hides_non_public_files(client, file_name):
    response = client.get(f"/db/{file_name}")

    assert response.status_code == 404
    assert "users" not in response.text
    assert "participants" not in response.text
```

Adicionar um caso que altera `SCHEDULE_PATH` e `SETTINGS_PATH` depois da primeira requisição, escreve novos documentos válidos e confirma que a segunda requisição lê os novos caminhos. Adicionar casos de arquivo ausente e diretório no caminho, sempre com 404 sem o caminho absoluto.

- [ ] **Step 2: Executar para confirmar a falha**

```powershell
uv run pytest tests/test_routing_contract.py tests/test_public_site.py -q
```

Esperado: os quatro `GET /db/*.json` retornam 404 porque ainda não existe uma rota de dados antes do mount estático.

- [ ] **Step 3: Implementar a resolução allowlisted por requisição**

Em `routes/site.py`, declarar um mapa explícito de factories e uma rota raiz fora do prefixo `/api`:

```python
PUBLIC_JSON_PATH_FACTORIES = {
    "schedule.json": get_schedule_path,
    "locations.json": get_locations_path,
    "knowledge_axes.json": get_knowledge_axes_path,
    "settings.json": get_settings_path,
}


@router.get("/db/{file_name}", include_in_schema=False)
def public_json(file_name: str) -> FileResponse:
    factory = PUBLIC_JSON_PATH_FACTORIES.get(file_name)
    if factory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Não encontrado")
    path = factory()
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Não encontrado")
    return FileResponse(
        path,
        media_type="application/json",
        headers={"Cache-Control": "no-cache"},
    )
```

O `detail` deve ser genérico e a rota deve comparar o nome completo antes de consultar o path. Registrar `site.router` em `app.py` antes de `app.mount("/", ...)`. Não adicionar handlers mutáveis, leitura autenticada ou chamadas de client de gravação.

- [ ] **Step 4: Executar os testes da rota**

```powershell
uv run pytest tests/test_routing_contract.py tests/test_public_site.py -q
uv run ruff check routes/site.py app.py tests/test_routing_contract.py tests/test_public_site.py
```

Esperado: quatro documentos acessíveis, nomes proibidos em 404, headers corretos e caminhos reavaliados entre chamadas.

- [ ] **Step 5: Fazer commit**

```powershell
git add routes/site.py app.py tests/test_routing_contract.py tests/test_public_site.py
git commit -m "Publica JSONs permitidos para o site"
```

### Task 4: Fixar o contrato JavaScript com testes vermelhos

**Files:**
- Create: `tests/site/test_schedule_js.py`
- Modify: `static/site/js/schedule.js` only after the failing run in this task

**Interfaces:**
- Consumes: o script atual carregado em um contexto Node sem `document`.
- Produces: nomes e assinaturas que a implementação das Tasks 5 e 6 deve preservar: `loadPublicDocuments`, `findCompleteProgramSection`, `normalizeScheduleDocument`, `statusForActivity`, `deriveShiftView`, `deriveAxisView`, `selectCarouselActivities` e `renderGroups`.

- [ ] **Step 1: Criar um harness Node isolado**

Em `tests/site/test_schedule_js.py`, usar `subprocess.run(["node", "-", str(SCHEDULE_SCRIPT)])` e `vm.runInNewContext` para importar `module.exports` sem criar DOM. O caso deve falhar com mensagem clara se o script não exportar uma função:

```python
def run_node_case(case: str) -> None:
    source = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const scheduleModule = {{exports: {{}}}};
const script = fs.readFileSync(process.argv[2], "utf8");
vm.runInNewContext(script, {{module: scheduleModule, exports: scheduleModule.exports, console}});
const api = scheduleModule.exports;
{case}
"""
    completed = subprocess.run(
        ["node", "-", str(SCHEDULE_SCRIPT)],
        input=source,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
```

- [ ] **Step 2: Escrever os casos de normalização e segurança**

Cobrir, com payloads mínimos:

```javascript
const schedule = {
  version: 1,
  sections: [{id: "complete-program", title: "Completa", groups: [
    {id: "sem-eixo", title: "Grupo <seguro>", knowledgeAxis: null, items: [
      {id: "atividade-1", title: "Título <seguro>", description: "Descrição", sessions: [
        {startTime: "11:59", endTime: "12:00", locations: ["Sala A", "Sala B"]}
      ]}
    ]},
    {id: "eixo-desconhecido", title: "Outro", knowledgeAxis: "axis-secret", items: []}
  ]}]
};
const normalized = api.normalizeScheduleDocument(
  schedule,
  {knowledgeAxes: [{id: "axis-real", name: "Eixo real"}]},
  {locations: [{name: "Sala A"}, {name: "Sala B"}]},
  {eventDate: "2026-09-22"},
);
assert.equal(normalized.eventDate, "2026-09-22");
assert.equal(normalized.section.groups[0].knowledgeAxis, null);
assert.equal(normalized.section.groups[0].items[0].sessions[0].location, "Sala A · Sala B");
assert.equal(normalized.section.groups[1].knowledgeAxis, "axis-secret");
assert.deepEqual(schedule.sections[0].groups[0].items[0].sessions[0].locations, ["Sala A", "Sala B"]);
```

Adicionar também um caso que faça `loadPublicDocuments()` rejeitar quando qualquer resposta tiver `ok === false` ou quando `response.json()` lançar; o teste Node deve concentrar apenas carregamento e funções puras.

- [ ] **Step 3: Escrever os casos de intervalos, eixos e estados temporais**

Usar `Date("2026-09-22T...")` e `America/Sao_Paulo` para fixar:

```javascript
assert.equal(
  api.statusForActivity(
    [{startTime: "10:00", endTime: "11:00"}],
    "2026-09-22",
    new Date("2026-09-22T13:30:00.000Z"),
    "America/Sao_Paulo",
  ),
  "AO VIVO",
);
assert.equal(
  api.statusForActivity(
    [{startTime: "10:00", endTime: "11:00"}],
    "2026-09-22",
    new Date("2026-09-22T14:00:00.000Z"),
    "America/Sao_Paulo",
  ),
  "FINALIZADA",
);
assert.equal(
  api.statusForActivity(
    [{startTime: "10:00", endTime: "11:00"}],
    "2026-09-21",
    new Date("2026-09-21T12:00:00.000Z"),
    "America/Sao_Paulo",
  ),
  "EM BREVE",
);
```

Também afirmar que `[12:00, 18:00)` pertence à tarde, `[18:00, 21:01)` à noite, eixo nulo/desconhecido cria o grupo textual `Sem eixo` e `selectCarouselActivities` devolve no máximo cinco IDs distintos na ordem de prioridade definida pela spec.

- [ ] **Step 4: Executar o harness antes da implementação**

```powershell
uv run pytest tests/site/test_schedule_js.py -q
```

Esperado: falha, pois as funções novas ainda não existem e a implementação atual usa `eventDate` da agenda e constantes de eixos.

- [ ] **Step 5: Fazer commit dos testes vermelhos**

```powershell
git add tests/site/test_schedule_js.py
git commit -m "Cobre contrato da agenda pública"
```

### Task 5: Reescrever a normalização e renderização da agenda pública

**Files:**
- Modify: `static/site/js/schedule.js`
- Modify: `tests/site/test_schedule_js.py` when a test needs a narrower assertion

**Interfaces:**
- Consumes: quatro documentos retornados por `loadPublicDocuments(fetchImpl, baseURI)`.
- Produces: um view model sem mutação do JSON, visões por turno/eixo, estados textuais e renderização DOM com `textContent`/atributos.

- [ ] **Step 1: Implementar o carregamento paralelo estrito**

Adicionar:

```javascript
async function loadPublicDocuments(fetchImpl = fetch, baseURI = document.baseURI) {
  const files = ["schedule.json", "knowledge_axes.json", "locations.json", "settings.json"];
  const responses = await Promise.all(
    files.map((fileName) => fetchImpl(new URL(`/db/${fileName}`, baseURI))),
  );
  if (responses.some((response) => !response.ok)) {
    throw new Error("Falha ao carregar os dados públicos");
  }
  const documents = await Promise.all(responses.map((response) => response.json()));
  return {
    schedule: documents[0],
    knowledgeAxes: documents[1],
    locations: documents[2],
    settings: documents[3],
  };
}
```

Rejeitar resposta que não seja objeto, exigir `settings.eventDate` e nunca tentar `/api` ou fallback de HTML persistido.

- [ ] **Step 2: Substituir as fontes codificadas pela normalização dos catálogos**

Remover `GUIDING_AXES`, `COURSE_AXIS_MAP` e qualquer data padrão. Implementar `findCompleteProgramSection(document)`, `createKnowledgeAxisMap(document)` e `createLocationMap(document)`. `normalizeScheduleDocument(schedule, axes, locations, settings)` deve retornar `eventDate: settings.eventDate`, grupos na ordem original e sessões com uma propriedade de apresentação `location` formada por nomes não vazios unidos por ` · `.

O view model deve conservar `knowledgeAxis: null` e referências desconhecidas; a decisão de agrupamento em `Sem eixo` ficará em `deriveAxisView`, não em uma tentativa de inventar eixo pelo ID do curso.

- [ ] **Step 3: Implementar o relógio local e os estados textuais**

Manter `localDateAndMinutes(now, "America/Sao_Paulo")` usando `Intl.DateTimeFormat`. Implementar:

```javascript
function statusForActivity(sessions, eventDate, now, timeZone = "America/Sao_Paulo") {
  const localNow = localDateAndMinutes(now, timeZone);
  if (localNow.date < eventDate) return "EM BREVE";
  if (localNow.date > eventDate) return "FINALIZADA";
  const validSessions = (sessions || []).filter(
    (session) => session.startTime && session.endTime,
  );
  if (validSessions.some((session) => {
    const interval = sessionInterval(session);
    return interval.startMinutes <= localNow.minutes && localNow.minutes < interval.endMinutes;
  })) return "AO VIVO";
  if (validSessions.some((session) => timeToMinutes(session.startTime) > localNow.minutes)) {
    return "EM BREVE";
  }
  return validSessions.length ? "FINALIZADA" : "EM BREVE";
}
```

Usar o retorno em todos os cards. O estado final deve ser comunicado por texto e classe/atributo, nunca somente por cor.

- [ ] **Step 4: Implementar derivação por turno e por eixo**

Preservar `SHIFTS`, `overlapsShift` e a ordem do JSON. `deriveShiftView(section, eventDate, now, timeZone)` deve incluir a atividade em todo turno cujo intervalo tenha sobreposição estrita (`start < shift.end` e `end > shift.start`) e calcular o estado com as sessões exibidas.

`deriveAxisView(section, knowledgeAxes, eventDate, now, timeZone)` deve criar um grupo para cada eixo vindo do catálogo, seguido de um grupo `Sem eixo` quando houver grupo nulo ou desconhecido. Nenhum grupo da seção pode desaparecer; cada atividade deve continuar sob o título do grupo vindo do JSON.

- [ ] **Step 5: Renderizar DOM sem interpolar conteúdo persistido**

Reescrever `renderItemCard`, `renderSession` e `renderGroups` para criar elementos com `document.createElement`, `textContent`, `setAttribute` e propriedades DOM. Para links, aceitar apenas o valor já validado pelo backend, usar `target="_blank"` e `rel="noopener noreferrer"`. Não usar `innerHTML` para títulos, descrições, locais, horários, IDs ou links.

Cada item deve receber `data-schedule-item`, `data-schedule-status` e uma classe correspondente; o badge deve conter exatamente o estado textual. Manter `aria-labelledby`, radio group, `aria-checked`, `tabindex`, `aria-live` e `aria-busy`. Ao re-renderizar, guardar IDs de `<details open>` e restaurar somente os grupos equivalentes.

- [ ] **Step 6: Implementar seleção e renderização do carrossel a partir das atividades**

Adicionar `flattenActivities(section, eventDate, now, timeZone)` e `selectCarouselActivities(activities, eventDate, now, timeZone)`. Usar um `Set` de IDs, limitar a cinco itens e manter a ordem original como desempate. No dia do evento, ordenar `AO VIVO` antes das próximas; antes do evento usar as próximas; depois do evento usar as últimas. Renderizar no `.carousel-track` somente textos de título, descrição, horário e locais vindos dos documentos; remover tags e títulos fictícios do HTML.

Depois de substituir o trilho, chamar `window.initializeCarousel?.()` para que a Task 6 monte os indicadores e clones.

- [ ] **Step 7: Implementar inicialização, sucesso e falha silenciosa**

`initCompleteProgram()` deve encontrar o shell, marcar `[data-schedule-root]` como `aria-busy="true"`, carregar os quatro JSONs, renderizar o modo atualmente selecionado e montar o carrossel. Em sucesso, usar `aria-busy="false"`; em qualquer falha de rede, HTTP ou parse, limpar somente o estado ocupado, deixar agenda/carrossel vazios e retornar sem mensagem técnica, retry ou chamada administrativa.

Exportar por `window.CompleteProgram` e CommonJS as funções puras usadas pelos testes, inclusive `loadPublicDocuments` e `statusForActivity`.

- [ ] **Step 8: Executar os testes unitários JavaScript**

```powershell
uv run pytest tests/site/test_schedule_js.py -q
```

Esperado: todos os casos vermelhos da Task 4 passam; a implementação não acessa `eventDate` em `schedule.json`, não usa constantes de eixos e não altera o objeto de entrada.

- [ ] **Step 9: Fazer commit**

```powershell
git add static/site/js/schedule.js tests/site/test_schedule_js.py
git commit -m "Renderiza agenda pública dos JSONs"
```

### Task 6: Tornar o carrossel idempotente e remover dados do shell HTML

**Files:**
- Modify: `static/site/js/carousel.js`
- Modify: `static/site/index.html`
- Modify: `static/site/css/main.css`, `static/site/css/schedule.css`
- Modify: `tests/site/browser_support.py`, `tests/site/test_identity_hero.py`, `tests/site/test_carousel.py`

**Interfaces:**
- Consumes: `window.initializeCarousel()` chamada pela Task 5 depois que o trilho possui cards.
- Produces: shell sem agenda persistida, carrossel com no máximo cinco cards reais e comportamento existente de teclado/toque/resize/autoplay.

- [ ] **Step 1: Escrever o teste de shell sem dados e inicialização repetida**

Em `tests/test_public_site.py` ou `tests/site/test_identity_hero.py`, afirmar que o HTML inicial não contém uma atividade real conhecida, `eventDate`, `data-schedule-item` ou card `.activity-card`. No browser, montar um pequeno card por `evaluate`, chamar `window.initializeCarousel()` duas vezes e afirmar:

```javascript
const track = document.querySelector(".carousel-track");
if (track.querySelectorAll("[data-carousel-clone]").length !== 0) throw new Error("clones inesperados");
window.initializeCarousel();
window.initializeCarousel();
if (track.querySelectorAll(".activity-card:not([data-carousel-clone])").length !== 1) throw new Error("cards duplicados");
if (document.querySelectorAll(".carousel-dots .dot").length !== 1) throw new Error("dots duplicados");
```

Atualizar o teste de falha para esperar cards vazios, hero/regulamento/mapa disponíveis e `aria-busy="false"`, em vez de depender de fallback com cards hardcoded.

- [ ] **Step 2: Executar o teste antes da mudança**

```powershell
uv run pytest tests/test_public_site.py tests/site/test_identity_hero.py -q
```

Esperado: falha porque o HTML atual possui cards fictícios e `carousel.js` captura o trilho somente uma vez antes da agenda dinâmica.

- [ ] **Step 3: Expor uma inicialização idempotente do carrossel**

Reestruturar o IIFE de `static/site/js/carousel.js` para definir `initializeCarousel(root = document.querySelector(".carousel"))`. Guardar uma instância por elemento com `WeakMap`; a primeira chamada instala listeners, e chamadas seguintes atualizam a lista de cards reais e executam `rebuild()` sem instalar listeners novamente.

O `rebuild()` deve:

1. remover clones anteriores;
2. reler `track.children` que não tenham `data-carousel-clone`;
3. gerar páginas conforme os breakpoints existentes;
4. desabilitar setas e deixar dots vazios quando não houver cards;
5. preservar página próxima e foco do indicador após resize;
6. manter gap de 20px, medição fracionada, duração proporcional, loop, swipe, setas, teclado, autoplay de 8s e `prefers-reduced-motion`.

Cada clone deve continuar com `data-carousel-clone`, `aria-hidden="true"`, `inert` e sem IDs. Expor a função em `window.initializeCarousel` e manter uma inicialização automática que não falhe quando o trilho ainda estiver vazio.

- [ ] **Step 4: Reduzir o HTML ao shell público**

Em `static/site/index.html`:

- manter `lang="pt-BR"`, hero, landmarks, regulamento, mapas, headings e scripts;
- deixar `.carousel-track` vazio, sem comentários/cards fictícios, com os controles e dots presentes;
- manter a seção `#complete-program` com o título, seletor acessível e `.schedule-view-groups` vazio;
- iniciar `[data-schedule-root]` com `aria-busy="true"`;
- manter um `<noscript>` que informe que JavaScript é necessário para consultar a programação;
- remover do HTML toda data, título, descrição, horário, local, eixo, ID e status oriundos dos JSONs.

Não remover os assets do hero nem alterar o texto estático do regulamento e do mapa.

- [ ] **Step 5: Ajustar estilos somente para os estados reais**

Em `main.css` e `schedule.css`, estilizar `live`, `soon` e `finalized` com os tokens semânticos existentes (`--color-status-*`, `--color-finalized-*`, `--color-focus` etc.). Não adicionar literais de paleta. O estado finalizado da agenda e o badge do carrossel devem ter texto; focus-visible, alvos de toque, overflow e `prefers-reduced-motion` devem continuar iguais ao contrato.

- [ ] **Step 6: Fazer o servidor de browser disponibilizar fixtures dos quatro JSONs**

Em `tests/site/browser_support.py`, manter o servidor estático para `static/site/` e acrescentar uma tabela segura para `/db/schedule.json`, `/db/knowledge_axes.json`, `/db/locations.json` e `/db/settings.json`, lendo os arquivos de `db/` sem permitir que qualquer outro caminho seja servido. Isso mantém os testes do site sem copiar JSONs para `static/site/`.

- [ ] **Step 7: Executar a suíte de interação pública**

```powershell
uv run pytest tests/test_public_site.py tests/test_home_page.py tests/site -q
```

Esperado: o HTML não contém a programação, os cards reais chegam pelos JSONs, o carrossel continua com 1/2/3 cards por página, clones ficam inacessíveis, swipe/teclado/resize/autoplay continuam funcionando e falha de rede não apaga o restante da página.

- [ ] **Step 8: Fazer commit**

```powershell
git add static/site/js/carousel.js static/site/index.html static/site/css/main.css static/site/css/schedule.css tests/site/browser_support.py tests/site/test_identity_hero.py tests/site/test_carousel.py tests/test_public_site.py tests/test_home_page.py
git commit -m "Integra carrossel dinâmico ao shell público"
```

### Task 7: Cobrir rede real, simulação de live event e documentação das fronteiras

**Files:**
- Modify: `tests/site/test_identity_hero.py` or create `tests/site/test_public_schedule.py`
- Modify: `tests/site/browser_support.py` if the fixture needs per-page overrides
- Modify: `tests/test_public_site.py`, `tests/test_routing_contract.py`
- Modify: `static/site/DESIGN.md`
- Modify: `ARCHITECTURE.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: rota pública da Task 3 e runtime do site das Tasks 5–6.
- Produces: evidência de que a agenda real aparece, a data isolada simula `AO VIVO`, falhas são silenciosas e a documentação reflete a arquitetura entregue.

- [ ] **Step 1: Escrever o teste de rede e fonte de verdade**

Adicionar um teste Playwright que registre `request.method` e URL durante o carregamento e confirme:

```python
assert {
    (request.method, request.url.rsplit("/", 1)[-1])
    for request in requests
    if "/db/" in request.url
} == {
    ("GET", "schedule.json"),
    ("GET", "knowledge_axes.json"),
    ("GET", "locations.json"),
    ("GET", "settings.json"),
}
assert not any("/api/" in request.url for request in requests)
assert (
    page.locator(".schedule-item")
    .filter(has_text="Voz e Ação: conhecendo o curso de Administração")
    .count()
    > 0
)
assert page.locator(".activity-card").filter(has_text="Visita guiada ao Campus").count() == 0
```

O título esperado deve ser um título real presente em `db/schedule.json`; o título fictício atual deve permanecer ausente.

- [ ] **Step 2: Escrever o teste determinístico de `AO VIVO`**

Interceptar apenas `settings.json` com `{"eventDate": "2026-09-22"}` e instalar o relógio do Playwright em um horário dentro de uma sessão conhecida do fixture, por exemplo 09:00–10:00. Confirmar um `.schedule-item__status` com texto `AO VIVO` e que o documento servido de `schedule.json` não foi alterado. Repetir com um horário antes do início (`EM BREVE`) e após o fim (`FINALIZADA`) sem mudar a agenda.

- [ ] **Step 3: Escrever o teste de falha de rede e fronteira de escrita**

Abortar os quatro requests de `/db/*.json`, aguardar o carregamento e afirmar que:

```python
assert page.locator(".hero-image").count() == 1
assert page.get_by_role("heading", name="Regulamento da Gincana").is_visible()
assert page.locator(".campus-map-img").count() > 0
assert page.locator("[data-schedule-root]").get_attribute("aria-busy") == "false"
assert page.locator(".schedule-item").count() == 0
assert not any(request.method in {"PUT", "POST", "PATCH", "DELETE"} for request in requests)
```

Capturar `pageerror` e exigir lista vazia; não esperar mensagem técnica ou retry.

- [ ] **Step 4: Atualizar o contrato público em `static/site/DESIGN.md`**

Substituir a frase que descreve a agenda como futura integração por uma regra ativa: `schedule.json`, `knowledge_axes.json`, `locations.json` e `settings.json` chegam por `GET /db/{file_name}`, somente leitura, com `eventDate` exclusivamente nas configurações. Registrar que o site não usa `/api`, que o HTML inicial contém somente shells e que falha de rede deixa a página estática utilizável. Documentar os rótulos textuais e a simulação por `SETTINGS_PATH` sem criar tokens ou componentes administrativos.

- [ ] **Step 5: Atualizar arquitetura e README**

Em `ARCHITECTURE.md`, atualizar o diagrama e as responsabilidades para incluir `routes/site.py` como entrega pública allowlisted, `clients.settings`, `/api/settings` e a separação entre configuração temporal e agenda. Em `README.md`, remover a indicação de integração futura, listar `SETTINGS_PATH` nos ambientes isolados e explicar em português:

```powershell
$env:SETTINGS_PATH = "C:\\caminho\\settings-simulacao.json"
uv run uvicorn app:app --reload --env-file .env
```

O arquivo isolado deve conter somente `{"eventDate": "2026-09-22"}`; a agenda continua em `SCHEDULE_PATH` e o navegador continua sem permissão de escrita.

- [ ] **Step 6: Executar os testes de rede e verificar a documentação**

```powershell
uv run pytest tests/test_public_site.py tests/test_routing_contract.py tests/site -q
rg -n "GET /db|SETTINGS_PATH|eventDate|/api/|somente leitura" static/site/DESIGN.md ARCHITECTURE.md README.md
```

Esperado: os documentos registram uma única fonte de verdade, a rota pública não é confundida com a API administrativa e os testes comprovam a simulação sem escrita.

- [ ] **Step 7: Fazer commit**

```powershell
git add tests/site static/site/DESIGN.md ARCHITECTURE.md README.md tests/test_public_site.py tests/test_routing_contract.py
git commit -m "Documenta contrato público da agenda"
```

### Task 8: Executar a verificação completa e preparar a revisão final

**Files:**
- Modify: nenhum arquivo de produto; corrigir apenas regressões encontradas nas tarefas anteriores antes de prosseguir.
- Test: suíte Python, JavaScript, site e E2E existentes.

**Interfaces:**
- Consumes: toda a implementação das Tasks 1–7.
- Produces: resultados reproduzíveis e uma árvore sem artefatos temporários previstos no repositório.

- [ ] **Step 1: Rodar testes unitários e de contrato**

```powershell
uv run pytest -q
```

Esperado: toda a suíte unitária e de contrato passa; `tests/conftest.py` remove `.pytest_cache`, `.pytest-tmp-unit` e `.pytest-tmp-*` ao terminar.

- [ ] **Step 2: Rodar site e E2E com Chromium**

Se o navegador ainda não estiver instalado, executar primeiro `uv run playwright install chromium`. Depois:

```powershell
uv run pytest tests/site -q
uv run pytest tests/e2e -q
```

Esperado: desktop, 768px e 390px não apresentam overflow; teclado, setas, swipe, loop, resize, foco, clones, autoplay e movimento reduzido passam; o painel continua autenticado e grava agenda/configuração separadamente.

- [ ] **Step 3: Rodar validações estáticas**

```powershell
uv run ruff check .
uv run ruff format --check .
uv run ty check
git diff --check
```

Corrigir todos os resultados antes da revisão visual. Não deixar `.pytest_cache`, `.pytest-tmp-unit` ou `.pytest-tmp-*` no workspace.

- [ ] **Step 4: Fazer auditoria de contrato de dados e rede**

Executar:

```powershell
rg -n '"eventDate"|eventDate|event_date' db models clients routes static/site static/admin tests
rg -n 'fetch\([^\n]*api|/api/(schedule|locations|knowledge-axes|settings)|method\s*:\s*["'"'](PUT|POST|PATCH|DELETE)' static/site/js
git ls-files db/settings.json db/schedule.json
git status --short
```

Confirmar manualmente que `eventDate` canônico aparece em `db/settings.json`, `models/settings.py`, `/api/settings`, admin e testes correspondentes, mas não em `db/schedule.json` nem em `static/site/index.html`; confirmar que os arquivos preexistentes fora do escopo não foram removidos ou adicionados ao commit.

- [ ] **Step 5: Registrar resultados da verificação**

Anotar no handoff do trabalho os comandos executados, seus resultados, os viewports verificados, o teste de `AO VIVO` com fixture de `settings.json` e a confirmação de que `static/admin/DESIGN.md` permaneceu sem alterações.

### Task 9: Revisar contratos de design

**Files:**
- Review: `static/site/DESIGN.md`, `static/site/index.html`, `static/site/js/schedule.js`, `static/site/js/carousel.js`, `static/site/css/main.css`, `static/site/css/schedule.css`
- Confirm unchanged: `static/admin/DESIGN.md` e tokens/componentes administrativos
- Test: `tests/site`, inspeção visual e diff final

**Interfaces:**
- Consumes: implementação verificada da Task 8.
- Produces: evidência final de conformidade visual e commit final somente depois desta revisão.

- [ ] **Step 1: Conferir fonte de verdade e segurança do frontend**

Verificar contra cada contrato aplicável de `static/site/DESIGN.md` que o HTML é somente shell, os quatro JSONs são lidos por `GET`, o site não chama `/api`, títulos/descrições/locais/links usam `textContent` e atributos DOM, e `settings.eventDate` é a única fonte da data.

- [ ] **Step 2: Conferir tokens, ícones e estados**

Inspecionar o diff e as regras computadas para confirmar que novas regras usam tokens semânticos, SVGs mantêm `currentColor`/`aria-hidden` quando decorativos, `AO VIVO`/`EM BREVE`/`FINALIZADA` aparecem como texto e nenhum literal de cor ou componente paralelo foi criado.

- [ ] **Step 3: Conferir acessibilidade e foco**

Com teclado, validar `lang="pt-BR"`, landmarks, headings, `aria-labelledby`, `role="radiogroup"`, `role="radio"`, `aria-checked`, `aria-busy`, `aria-live`, foco visível nos seletores, dots, setas e `<details>`, além de clones com `aria-hidden="true"` e `inert`.

- [ ] **Step 4: Conferir responsividade e movimento reduzido**

Executar a inspeção em 390px, 768px, 1440px e zoom fracionado. Confirmar ausência de overflow/recorte, alvos de toque preservados, gap e breakpoints do carrossel sincronizados, loop nos dois sentidos, resize com foco/página preservados e troca imediata sob `prefers-reduced-motion`.

- [ ] **Step 5: Confirmar a fronteira administrativa e registrar evidências**

Verificar `git diff --name-only -- static/admin/DESIGN.md` sem saída, comparar o painel com `static/admin/DESIGN.md` sem alterar tokens, e registrar no handoff os testes e inspeções que comprovam cada item desta tarefa. Esta tarefa deve ser concluída antes de qualquer commit final.

- [ ] **Step 6: Fazer o commit final depois da revisão**

```powershell
git add .
git commit -m "Conclui agenda pública orientada por JSON"
```

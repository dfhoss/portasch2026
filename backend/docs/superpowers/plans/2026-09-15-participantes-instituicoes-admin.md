# Cadastro de Participantes e Instituições — Plano de Implementação

> **Para agentes de implementação:** use obrigatoriamente `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar este plano tarefa a tarefa. Os passos usam caixas de seleção (`- [ ]`) para acompanhamento.

**Objetivo:** implementar o CRUD autenticado de instituições e participantes na API e no painel administrativo, com CPF validado, catálogo inicial das escolas da Feira de Ciências e retenção documentada.

**Arquitetura:** a API seguirá a separação entre modelos Pydantic, clients de persistência JSON e routers finos autenticados por `CurrentTokenData`. O painel build-free existente em `backend/static/home/` ganhará as seções de instituições e participantes. A seção `science-fair` permanece, mas sem o grupo de equipes.

**Tecnologias:** Python 3.14+, FastAPI, Pydantic, JSON atômico, pytest, Ruff, ty, HTML/CSS/JavaScript sem build, `TestClient` e Playwright.

**Spec:** `backend/docs/superpowers/specs/2026-09-09-participantes-e-instituicoes-design.md`

## Restrições globais

- Antes de iniciar, leia `.worktrees/eixos-workspace/backend/DESIGN.md`, `.worktrees/eixos-workspace/backend/ARCHITECTURE.md` e `.worktrees/eixos-workspace/backend/AGENTS.md`; use-os como referência somente leitura e não altere a worktree.
- Todo endpoint administrativo exige `CurrentTokenData` e fica sob o prefixo `/api` no deployment.
- Resolva `INSTITUTIONS_PATH` e `PARTICIPANTS_PATH` no momento da chamada, com fallback para `db/institutions.json` e `db/participants.json`.
- Use `atomic_write_json`; converta falhas de filesystem em `PersistenceError` sem expor caminhos na resposta HTTP.
- Normalize nomes por Unicode, espaços e caixa; preserve IDs ao atualizar.
- Normalize CPF para 11 dígitos, valide os dígitos verificadores, imponha unicidade e mascare-o nas listas do painel.
- Siga os tokens semânticos, acessibilidade e breakpoints de `backend/DESIGN.md`.
- Não altere credenciais, `backend/db/users.json` ou arquivos não relacionados.

## Mapa de arquivos

- Criar `backend/models/institutions.py` e `backend/models/participants.py` para contratos Pydantic.
- Criar `backend/clients/institutions.py` e `backend/clients/participants.py` para caminhos, validação, CRUD e persistência.
- Criar `backend/routes/institutions.py` e `backend/routes/participants.py`; registrar ambos em `backend/app.py`.
- Modificar `backend/tests/conftest.py`; criar `backend/tests/test_participant_institution_clients.py` e `backend/tests/test_participant_institution_api.py`.
- Modificar `backend/static/home/index.html`, `home.js` e `home.css` para o painel.
- Atualizar testes de UI existentes em `backend/tests/test_home_page.py`, `test_home_editor_js.py`, `test_catalog_ui_contract.py` e `tests/e2e/test_home_panel.py`.
- Verificar `backend/db/institutions.json`, `backend/db/participants.json` e `backend/db/schedule.json`.

---

### Tarefa 1: Fixar os dados iniciais e os fixtures

**Arquivos:**
- Criar: `backend/db/participants.json`
- Modificar: `backend/db/institutions.json`, `backend/db/schedule.json`, `backend/tests/conftest.py`
- Testar: `backend/tests/test_participant_institution_clients.py`

**Interfaces:** `TemporaryDatabase` deverá expor `institutions` e `participants`; o seed terá `nextId: 12`, 11 escolas com `state: "SC"` e `city: "Chapecó"`, e nenhum participante.

- [ ] **Passo 1: escrever testes do seed**

```python
def test_science_fair_keeps_section_without_participating_teams():
    payload = read_json(Path(__file__).parents[1] / "db" / "schedule.json")
    section = next(item for item in payload["sections"] if item["id"] == "science-fair")
    assert section["groups"] == []

def test_institutions_seed_contains_eleven_schools():
    payload = read_json(Path(__file__).parents[1] / "db" / "institutions.json")
    assert payload["nextId"] == 12
    assert len(payload["institutions"]) == 11
    assert {item["state"] for item in payload["institutions"]} == {"SC"}
    assert {item["city"] for item in payload["institutions"]} == {"Chapecó"}
```

- [ ] **Passo 2: executar** `uv run pytest backend/tests/test_participant_institution_clients.py -k seed -v`; esperar falha enquanto o fixture e os dados não existirem.
- [ ] **Passo 3: manter somente a seção `science-fair` com `groups: []` e criar `participants.json` como `{ "nextId": 1, "participants": [] }`; atualizar o fixture para copiar os dois catálogos temporários.
- [ ] **Passo 4: executar novamente** o teste focado; esperar PASS e confirmar que nenhum dado real é escrito.
- [ ] **Passo 5: commitar:** `git add backend/db backend/tests/conftest.py backend/tests/test_participant_institution_clients.py; git commit -m "Prepara dados de instituicoes e participantes"`.

### Tarefa 2: Implementar instituições

**Arquivos:**
- Criar: `backend/models/institutions.py`, `backend/clients/institutions.py`
- Modificar: `backend/clients/json_store.py` apenas para exceções compartilhadas
- Testar: `backend/tests/test_participant_institution_clients.py`

**Interfaces:** `get_institutions_path() -> Path`; `InstitutionRepository(path: Path)` com `list()`, `get(institution_id)`, `create(name, state, city, description)`, `update(institution_id, name, state, city, description)` e `delete(institution_id)`.

- [ ] **Passo 1: escrever testes de CRUD e duplicidade**

```python
def test_institution_repository_normalizes_values_and_generates_id(tmp_path):
    path = tmp_path / "institutions.json"
    write_json(path, {"nextId": 1, "institutions": []})
    created = InstitutionRepository(path).create("  Escola  Nova ", "SC", "Chapecó", "  texto  ")
    assert created == {"id": "institution-001", "name": "Escola Nova", "state": "SC", "city": "Chapecó", "description": "texto"}

def test_institution_repository_rejects_equivalent_name(tmp_path):
    path = tmp_path / "institutions.json"
    write_json(path, {"nextId": 2, "institutions": [{"id": "institution-001", "name": "Escola Nova", "state": "SC", "city": "Chapecó", "description": None}]})
    with pytest.raises(DuplicateResourceNameError):
        InstitutionRepository(path).create(" ESCOLA   NOVA ", "SC", "Chapecó", None)
```

- [ ] **Passo 2: executar** `uv run pytest backend/tests/test_participant_institution_clients.py -k institution -v`; esperar falha por repository ausente.
- [ ] **Passo 3: implementar** validação estrutural, limites dos campos, normalização, IDs, cópia defensiva e `atomic_write_json`; lançar `ResourceNotFoundError`, `DuplicateResourceNameError`, `InvalidResourceNameError` e `PersistenceError` conforme o caso.
- [ ] **Passo 4: executar** `uv run pytest backend/tests/test_participant_institution_clients.py -k institution -v`; esperar PASS.
- [ ] **Passo 5: commitar** com `git add backend/models/institutions.py backend/clients/institutions.py backend/clients/json_store.py backend/tests/test_participant_institution_clients.py; git commit -m "Implementa client de instituicoes"`.

### Tarefa 3: Implementar participantes e CPF

**Arquivos:**
- Criar: `backend/models/participants.py`, `backend/clients/participants.py`
- Testar: `backend/tests/test_participant_institution_clients.py`

**Interfaces:** `normalize_cpf(value: str) -> str`; `get_participants_path() -> Path`; `ParticipantRepository(path: Path, institutions_path: Path)` com `list()`, `get(participant_id)`, `create(name, cpf, email, institution_id)`, `update(participant_id, name, cpf, email, institution_id)` e `delete(participant_id)`.

- [ ] **Passo 1: escrever testes do algoritmo e da integridade**

```python
@pytest.mark.parametrize("value", ["529.982.247-25", "52998224725"])
def test_normalize_cpf_accepts_valid_values(value):
    assert normalize_cpf(value) == "52998224725"

@pytest.mark.parametrize("value", ["111.111.111-11", "123", "529.982.247-26"])
def test_normalize_cpf_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        normalize_cpf(value)
```

- [ ] **Passo 2: executar** `uv run pytest backend/tests/test_participant_institution_clients.py -k cpf -v`; esperar falha.
- [ ] **Passo 3: implementar** remoção de máscara, rejeição de sequências repetidas, cálculo dos dois dígitos verificadores, unicidade com `DuplicateParticipantCpfError`, validação da instituição referenciada e persistência atômica.
- [ ] **Passo 4: escrever e executar** teste que cria participante, tenta CPF duplicado e instituição inexistente, e verifica `DuplicateParticipantCpfError`/`ResourceNotFoundError`; executar `uv run pytest backend/tests/test_participant_institution_clients.py -k "cpf or participant" -v` e esperar PASS.
- [ ] **Passo 5: testar exclusão protegida:** ao excluir instituição vinculada, esperar `ResourceInUseError` com IDs dos participantes e nenhum JSON alterado; commitar com `git add backend/models/participants.py backend/clients/participants.py backend/tests/test_participant_institution_clients.py; git commit -m "Implementa cadastro de participantes"`.

### Tarefa 4: Expor os CRUDs autenticados

**Arquivos:**
- Criar: `backend/routes/institutions.py`, `backend/routes/participants.py`
- Modificar: `backend/app.py`
- Testar: `backend/tests/test_participant_institution_api.py`

**Interfaces:** routers `/institutions` e `/participants` com `GET`, `POST`, `PUT /{id}` e `DELETE /{id}`; handlers recebem `CurrentTokenData`; erros mapeiam para `404`, `409`, `422` e `500` sem detalhes internos.

- [ ] **Passo 1: escrever testes HTTP**

```python
@pytest.mark.parametrize("path", ["/institutions", "/participants"])
def test_catalog_routes_require_authentication(client, path):
    assert client.get(path).status_code == status.HTTP_401_UNAUTHORIZED

def test_create_participant_returns_normalized_cpf(client, auth_headers):
    institution = client.get("/institutions", headers=auth_headers).json()[0]
    response = client.post("/participants", headers=auth_headers, json={"name": "Aluno", "cpf": "529.982.247-25", "email": "aluno@example.org", "institutionId": institution["id"]})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["cpf"] == "52998224725"
```

- [ ] **Passo 2: executar** `uv run pytest backend/tests/test_participant_institution_api.py -v`; esperar falha por routers ausentes.
- [ ] **Passo 3: implementar** dependencies dos repositories, `_run` de erro inspirado em `routes/locations.py`, registro dos routers em `app.py` e modelos de resposta.
- [ ] **Passo 4: cobrir e executar** CRUD, 401, 404, 409, 422, 500 não vazante, referência inexistente e exclusão de instituição vinculada; esperar PASS.
- [ ] **Passo 5: commitar** com `git add backend/routes backend/app.py backend/tests/test_participant_institution_api.py; git commit -m "Adiciona API de participantes e instituicoes"`.

### Tarefa 5: Criar o CRUD no painel administrativo

**Arquivos:** `backend/static/home/index.html`, `home.js`, `home.css`; testes em `backend/tests/test_home_page.py`, `test_home_editor_js.py`, `test_catalog_ui_contract.py` e `tests/e2e/test_home_panel.py`.

**Interfaces:** adicionar `institutions` e `participants` a `EDITOR_SECTIONS`; usar `apiFetch` com o token da sessão; mostrar instituições e participantes em listas pesquisáveis; usar diálogos para criar/editar e confirmação para excluir.

- [ ] **Passo 1: escrever testes de contrato**

```python
def test_admin_page_contains_new_catalog_sections(client):
    html = client.get("/home").text
    assert 'data-editor-section="institutions"' in html
    assert 'data-editor-section="participants"' in html
```

```javascript
test("participant list masks CPF", () => {
  const html = participantRow({name: "Aluno", cpf: "52998224725", institutionId: "institution-001"});
  expect(html).toContain("***.***.***-25");
  expect(html).not.toContain("52998224725");
});
```

- [ ] **Passo 2: executar** os testes de UI focados; esperar falhas pelos novos contratos.
- [ ] **Passo 3: implementar** navegação, estados vazios, tabelas/cards, busca, carregamento da relação de instituições e formulários com labels para nome, CPF, e-mail, estado, cidade e descrição.
- [ ] **Passo 4: implementar** máscara visual de CPF, envio normalizado, toasts, erros estruturados, foco no diálogo, confirmação de exclusão e bloqueio visual para instituição em uso.
- [ ] **Passo 5: validar responsividade e acessibilidade** conforme `DESIGN.md`; não inserir catálogos ou CPF no HTML inicial; atualizar `DESIGN.md` somente se novos tokens forem necessários.
- [ ] **Passo 6: executar** `uv run pytest backend/tests/test_home_page.py backend/tests/test_home_editor_js.py backend/tests/test_catalog_ui_contract.py -v` e `uv run pytest backend/tests/e2e -v` quando Chromium estiver instalado; commitar com `git add backend/static/home backend/tests; git commit -m "Adiciona CRUD ao painel administrativo"`.

### Tarefa 6: Validar documentação, segurança e entrega

**Arquivos:** `backend/docs/superpowers/specs/2026-09-09-participantes-e-instituicoes-design.md`, `TASKS.md`, `backend/ARCHITECTURE.md` e toda a suíte.

- [ ] **Passo 1: conferir cobertura da spec:** API, persistência, seed de 11 escolas, seção vazia da Feira, CPF, painel, autenticação, conflitos e retenção até `31/07/2027` devem estar representados nos testes ou na documentação.
- [ ] **Passo 2: revisar segurança:** CPF completo não aparece em listas, HTML inicial, logs ou fixtures; tokens e `users.json` não foram alterados.
- [ ] **Passo 3: executar dentro de `backend`** `uv run ruff check .`, `uv run ruff format --check .`, `uv run ty check` e `uv run pytest`; corrigir falhas antes do commit final.
- [ ] **Passo 4: revisar o diff** com `git diff --check` e `git status --short`; não incluir `ideas.md`, imagens não relacionadas ou alterações acidentais de dados.
- [ ] **Passo 5: atualizar `backend/ARCHITECTURE.md`** somente se a implementação alterar fronteiras descritas; registrar no commit final em português e imperativo.

## Checklist de conclusão

- [ ] `science-fair` existe e está com `groups: []`.
- [ ] As 11 escolas estão em `backend/db/institutions.json` como Chapecó/SC.
- [ ] CRUD autenticado funciona para instituições e participantes.
- [ ] CPF é válido, normalizado, único e mascarado no painel.
- [ ] Instituição vinculada não pode ser excluída.
- [ ] A página administrativa é acessível e responsiva.
- [ ] A retenção até `31/07/2027` continua documentada em `TASKS.md`; este plano não apaga dados automaticamente.
- [ ] Lint, tipagem e testes passam.

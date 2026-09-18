# Cadastro de Participantes e Instituições — Plano de Implementação

> **Para agentes de implementação:** use obrigatoriamente `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar este plano tarefa a tarefa. Os passos usam caixas de seleção (`- [ ]`) para acompanhamento.

**Objetivo:** implementar o CRUD autenticado de instituições e participantes na API e no painel administrativo, com CPF validado, catálogo inicial das escolas da Feira de Ciências e retenção documentada.

**Arquitetura:** a API seguirá a separação entre modelos Pydantic, clients de persistência JSON e routers finos autenticados por `CurrentTokenData`. O painel build-free existente em `backend/static/home/` ganhará as seções de instituições e participantes. A seção `science-fair` permanece, mas sem o grupo de equipes.

**Tecnologias:** Python 3.14+, FastAPI, Pydantic, JSON atômico, pytest, Ruff, ty, HTML/CSS/JavaScript sem build, `TestClient` e Playwright.

**Spec:** `backend/docs/superpowers/specs/2026-09-09-participantes-e-instituicoes-design.md`

## Estado da execução

Atualizado em 16/09/2026. As Tarefas 1 a 6 foram concluídas, revisadas e integradas em
`main`. A única tarefa pendente é a Tarefa 7, uma revisão final dos contratos de design
definidos em `backend/DESIGN.md`; as tarefas anteriores não devem ser reexecutadas.
Os relatórios anteriores estão em
`.superpowers/sdd/2026-09-15-participantes-instituicoes-admin/`.

## Restrições globais

- Antes de iniciar, leia `.worktrees/eixos-workspace/backend/DESIGN.md`, `.worktrees/eixos-workspace/backend/ARCHITECTURE.md` e `.worktrees/eixos-workspace/backend/AGENTS.md`; use-os como referência somente leitura e não altere a worktree.
- Todo endpoint administrativo exige `CurrentTokenData` e fica sob o prefixo `/api` no deployment.
- Resolva `INSTITUTIONS_PATH` e `PARTICIPANTS_PATH` no momento da chamada, com fallback para `db/institutions.json` e `db/participants.json`.
- Use `atomic_write_json`; converta falhas de filesystem em `PersistenceError` sem expor caminhos na resposta HTTP.
- Normalize nomes por Unicode, espaços e caixa; preserve IDs ao atualizar.
- Normalize CPF para 11 dígitos, valide os dígitos verificadores, imponha unicidade e mascare-o nas listas do painel.
- O dashboard autenticado deve ter visões funcionais de instituições e participantes,
  renderizadas via API após o login, com contagem, busca, estados vazio/carregando/erro e
  atualização após mutações; o HTML inicial continua sem catálogos e CPF completo.
- Siga os tokens semânticos, acessibilidade e breakpoints de `backend/DESIGN.md`.
- A última tarefa deste plano deve revisar a implementação contra todos os contratos aplicáveis
  de `backend/DESIGN.md`, incluindo ícones, tokens, acessibilidade, foco, responsividade e
  animações reduzidas.
- Execute a Tarefa 7 com um subagent criado pelo fluxo Superpowers e spawnado com
  `model: "gpt-5.6-luna"` e `reasoning_effort: "low"`.
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

- [x] **Passo 1: escrever testes do seed**

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
- [x] **Passo 3: manter somente a seção `science-fair` com `groups: []` e criar `participants.json` como `{ "nextId": 1, "participants": [] }`; atualizar o fixture para copiar os dois catálogos temporários.
- [x] **Passo 4: executar novamente** o teste focado; esperar PASS e confirmar que nenhum dado real é escrito.
- [x] **Passo 5: commitar:** `git add backend/db backend/tests/conftest.py backend/tests/test_participant_institution_clients.py; git commit -m "Prepara dados de instituicoes e participantes"`.

### Tarefa 2: Implementar instituições

**Arquivos:**
- Criar: `backend/models/institutions.py`, `backend/clients/institutions.py`
- Modificar: `backend/clients/json_store.py` apenas para exceções compartilhadas
- Testar: `backend/tests/test_participant_institution_clients.py`

**Interfaces:** `get_institutions_path() -> Path`; `InstitutionRepository(path: Path)` com `list()`, `get(institution_id)`, `create(name, state, city, description)`, `update(institution_id, name, state, city, description)` e `delete(institution_id)`.

- [x] **Passo 1: escrever testes de CRUD e duplicidade**

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
- [x] **Passo 3: implementar** validação estrutural, limites dos campos, normalização, IDs, cópia defensiva e `atomic_write_json`; lançar `ResourceNotFoundError`, `DuplicateResourceNameError`, `InvalidResourceNameError` e `PersistenceError` conforme o caso.
- [x] **Passo 4: executar** `uv run pytest backend/tests/test_participant_institution_clients.py -k institution -v`; esperar PASS.
- [x] **Passo 5: commitar** com `git add backend/models/institutions.py backend/clients/institutions.py backend/clients/json_store.py backend/tests/test_participant_institution_clients.py; git commit -m "Implementa client de instituicoes"`.

### Tarefa 3: Implementar participantes e CPF

**Arquivos:**
- Criar: `backend/models/participants.py`, `backend/clients/participants.py`
- Testar: `backend/tests/test_participant_institution_clients.py`

**Interfaces:** `normalize_cpf(value: str) -> str`; `get_participants_path() -> Path`; `ParticipantRepository(path: Path, institutions_path: Path)` com `list()`, `get(participant_id)`, `create(name, cpf, email, institution_id)`, `update(participant_id, name, cpf, email, institution_id)` e `delete(participant_id)`.

- [x] **Passo 1: escrever testes do algoritmo e da integridade**

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
- [x] **Passo 3: implementar** remoção de máscara, rejeição de sequências repetidas, cálculo dos dois dígitos verificadores, unicidade com `DuplicateParticipantCpfError`, validação da instituição referenciada e persistência atômica.
- [x] **Passo 4: escrever e executar** teste que cria participante, tenta CPF duplicado e instituição inexistente, e verifica `DuplicateParticipantCpfError`/`ResourceNotFoundError`; executar `uv run pytest backend/tests/test_participant_institution_clients.py -k "cpf or participant" -v` e esperar PASS.
- [x] **Passo 5: testar exclusão protegida:** ao excluir instituição vinculada, esperar `ResourceInUseError` com IDs dos participantes e nenhum JSON alterado; commitar com `git add backend/models/participants.py backend/clients/participants.py backend/tests/test_participant_institution_clients.py; git commit -m "Implementa cadastro de participantes"`.

### Tarefa 4: Expor os CRUDs autenticados

**Arquivos:**
- Criar: `backend/routes/institutions.py`, `backend/routes/participants.py`
- Modificar: `backend/app.py`
- Testar: `backend/tests/test_participant_institution_api.py`

**Interfaces:** routers `/institutions` e `/participants` com `GET`, `POST`, `PUT /{id}` e `DELETE /{id}`; handlers recebem `CurrentTokenData`; erros mapeiam para `404`, `409`, `422` e `500` sem detalhes internos.

- [x] **Passo 1: escrever testes HTTP**

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
- [x] **Passo 3: implementar** dependencies dos repositories, `_run` de erro inspirado em `routes/locations.py`, registro dos routers em `app.py` e modelos de resposta.
- [x] **Passo 4: cobrir e executar** CRUD, 401, 404, 409, 422, 500 não vazante, referência inexistente e exclusão de instituição vinculada; esperar PASS.
- [x] **Passo 5: commitar** com `git add backend/routes backend/app.py backend/tests/test_participant_institution_api.py; git commit -m "Adiciona API de participantes e instituicoes"`.

### Tarefa 5: Criar o CRUD no painel administrativo

**Arquivos:** `backend/static/home/index.html`, `home.js`, `home.css`; testes em `backend/tests/test_home_page.py`, `test_home_editor_js.py`, `test_catalog_ui_contract.py` e `tests/e2e/test_home_panel.py`.

**Interfaces:** adicionar `institutions` e `participants` a `EDITOR_SECTIONS`; usar `apiFetch` com o token da sessão; mostrar instituições e participantes em visões responsivas pesquisáveis; usar diálogos para criar/editar e confirmação para excluir.

**Visualizações obrigatórias:** a visão de instituições deve mostrar nome, cidade, estado e
quantidade total; a visão de participantes deve mostrar nome, CPF mascarado, e-mail,
instituição e quantidade total. Ambas devem distinguir carregamento, vazio, erro e nenhum
resultado de busca, e atualizar a lista após cada mutação bem-sucedida.

- [x] **Passo 1: escrever testes de contrato**

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

```javascript
test("catalog views render counts and empty states", () => {
  expect(renderInstitutionView([])).toContain("Nenhuma instituição cadastrada");
  expect(renderParticipantView([])).toContain("Nenhum participante cadastrado");
  expect(renderInstitutionView([{name: "Escola", city: "Chapecó", state: "SC"}])).toContain("1 instituição");
});
```

- [ ] **Passo 2: executar** os testes de UI focados; esperar falhas pelos novos contratos.
- [x] **Passo 3: implementar** navegação e as duas visões do dashboard, com contagem, estados de carregamento/vazio/erro/sem resultado, tabelas/cards, busca, carregamento da relação de instituições e formulários com labels para nome, CPF, e-mail, estado, cidade e descrição.
- [x] **Passo 4: implementar** máscara visual de CPF, envio normalizado, toasts, erros estruturados, foco no diálogo, confirmação de exclusão e bloqueio visual para instituição em uso.
- [x] **Passo 5: validar responsividade e acessibilidade** conforme `DESIGN.md`; confirmar que as duas visões mostram dados reais após o login, não inserir catálogos ou CPF no HTML inicial e atualizar `DESIGN.md` somente se novos tokens forem necessários.
- [x] **Passo 6: executar** `uv run pytest backend/tests/test_home_page.py backend/tests/test_home_editor_js.py backend/tests/test_catalog_ui_contract.py -v` e `uv run pytest backend/tests/e2e -v` quando Chromium estiver instalado; commitar com `git add backend/static/home backend/tests; git commit -m "Adiciona CRUD ao painel administrativo"`.

### Tarefa 6: Validar documentação, segurança e entrega

**Arquivos:** `backend/docs/superpowers/specs/2026-09-09-participantes-e-instituicoes-design.md`, `TASKS.md`, `backend/ARCHITECTURE.md` e toda a suíte.

- [x] **Passo 1: conferir cobertura da spec:** API, persistência, seed de 11 escolas, seção vazia da Feira, CPF, painel, autenticação, conflitos e retenção até `31/07/2027` devem estar representados nos testes ou na documentação.
- [x] **Passo 2: revisar segurança:** CPF completo não aparece em listas, HTML inicial, logs ou fixtures; tokens e `users.json` não foram alterados.
- [x] **Passo 3: executar dentro de `backend`** `uv run ruff check .`, `uv run ruff format --check .`, `uv run ty check` e `uv run pytest`; Ruff check, ty e pytest passaram, e a limitação do format check global está registrada no relatório.
- [x] **Passo 4: revisar o diff** com `git diff --check` e `git status --short`; não incluir `ideas.md`, imagens não relacionadas ou alterações acidentais de dados.
- [x] **Passo 5: atualizar `backend/ARCHITECTURE.md`** somente se a implementação alterar fronteiras descritas; registrar no commit final em português e imperativo.

### Tarefa 7: Revisar contratos de design da implementação (última tarefa)

**Objetivo:** conferir a implementação entregue contra todos os contratos de design definidos
em `backend/DESIGN.md`, corrigindo somente desvios comprovados e deixando evidência antes do
commit final.

**Arquivos:**
- Ler: `backend/DESIGN.md`, `backend/AGENTS.md` e `backend/ARCHITECTURE.md`.
- Revisar: `backend/static/home/index.html`, `home.js` e `home.css`.
- Testar: `backend/tests/test_home_page.py`, `test_home_editor_js.py`,
  `test_catalog_ui_contract.py` e `tests/e2e/test_home_panel.py`.
- Relatar: `.superpowers/sdd/2026-09-15-participantes-instituicoes-admin/task-7-report.md`.

**Execução:** usar `superpowers:subagent-driven-development` ou
`superpowers:executing-plans` e spawnar o subagent com `model: "gpt-5.6-luna"` e
`reasoning_effort: "low"`. Não reexecute as Tarefas 1 a 6 como implementação.

- [ ] **Passo 1: mapear os contratos** — listar cada item da barra lateral e cada componente
  alterado em `static/home/`, confrontando-o com `DESIGN.md`: ícone SVG visível ao lado de todo
  rótulo, estados ativo/inativo, nome acessível, foco, contraste, tokens semânticos,
  responsividade e `prefers-reduced-motion`.
- [ ] **Passo 2: escrever ou ampliar os testes de contrato** — cobrir a presença de ícone em
  todos os itens da barra lateral e os contratos de acessibilidade/foco que forem verificáveis
  por HTML, JavaScript ou E2E; registrar o RED antes de qualquer ajuste.
- [ ] **Passo 3: corrigir os desvios comprovados** — alterar somente `static/home/` e os testes
  diretamente relacionados, reutilizando tokens existentes; atualizar `DESIGN.md` apenas se
  uma regra nova e estável da interface for necessária.
- [ ] **Passo 4: validar a implementação** — executar `uv run pytest --basetemp
  .pytest-tmp-design-review tests/test_home_page.py tests/test_home_editor_js.py
  tests/test_catalog_ui_contract.py -q`, `uv run pytest --basetemp
  .pytest-tmp-design-review-e2e tests/e2e -q`, `uv run ruff check .`, `uv run ruff format
  --check .`, `uv run ty check` e `git diff --check`; registrar falhas de baseline sem
  mascará-las.
- [ ] **Passo 5: fazer self-review e entregar** — confirmar que os dados do usuário,
  `ideas.md`, credenciais e arquivos não relacionados não entraram no diff; escrever o relatório
  com contratos verificados, evidências, arquivos e limitações; fazer commit curto, imperativo
  e em português somente depois de todas as verificações.

## Checklist de conclusão

- [x] `science-fair` existe e está com `groups: []`.
- [x] As 11 escolas estão em `backend/db/institutions.json` como Chapecó/SC.
- [x] CRUD autenticado funciona para instituições e participantes.
- [x] CPF é válido, normalizado, único e mascarado no painel; a listagem da API também retorna
  somente a máscara, enquanto o detalhe autenticado preserva o valor para edição.
- [x] Instituição vinculada não pode ser excluída.
- [x] A página administrativa é acessível e responsiva.
- [x] A retenção até `31/07/2027` continua documentada em `TASKS.md`; este plano não apaga dados automaticamente.
- [x] Ruff check, tipagem e testes passam; o format check global permanece limitado por arquivos preexistentes fora do escopo.
- [ ] A Tarefa 7 revisou todos os contratos de design de `backend/DESIGN.md` e registrou suas evidências.

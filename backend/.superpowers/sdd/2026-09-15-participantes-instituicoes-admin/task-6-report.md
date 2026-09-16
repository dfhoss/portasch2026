# Relatório da Tarefa 6

Data: 15/09/2026  
Base auditada: `c3b5993 Valida fluxos visuais dos catálogos`

## Checklist requisito a requisito

- [x] API: CRUD autenticado de instituições e participantes, incluindo 401, 404,
  409, 422, 500 e referência inexistente, coberto por `test_participant_institution_api.py`.
- [x] Persistência: caminhos configuráveis, validação estrutural, cópia defensiva,
  atomicidade e integridade entre catálogos cobertas por
  `test_participant_institution_clients.py`.
- [x] Seed: `db/institutions.json` contém `nextId: 12` e as 11 escolas exigidas,
  todas com `city: "Chapecó"` e `state: "SC"`.
- [x] Feira: `db/schedule.json` mantém `science-fair` com `groups: []`, sem
  `participating-teams`.
- [x] CPF: normalização, dígitos verificadores, rejeição de duplicidade e máscara
  visual estão cobertas por testes de client, API e painel.
- [x] Painel: as duas visões reais, contagem, busca, estados, CRUD, atualização,
  foco e responsividade têm contratos JavaScript e E2E autenticado.
- [x] Autenticação: rotas protegidas e fluxo do painel usam o JWT existente; o shell
  inicial não contém catálogos nem registros pessoais.
- [x] Conflitos: instituição vinculada não é excluída e o conflito preserva dados e
  informa referências.
- [x] Retenção: `TASKS.md` mantém a exclusão prevista até `31/07/2027`; esta tarefa
  não apaga dados automaticamente.

## Auditoria de segurança

`rg` não encontrou CPF completo em HTML inicial, logs, catálogos persistidos ou
fixtures de dados. Os CPFs literais encontrados estão exclusivamente em testes como
entradas sintéticas de validação; o painel lista apenas `***.***.***-NN` e o teste E2E
confirma que o CPF completo não aparece no DOM. `.env`, `db/users.json` e tokens não
foram alterados. `db/locations.json` e `../ideas.md` foram preservados fora da entrega.

## Validações executadas

- `uv run ruff check .` — passou: `All checks passed!`
- `uv run ruff format --check .` — falhou no baseline: 5 arquivos seriam formatados e
  36 já estão formatados; não foram reformatações aplicadas para evitar alterações fora
  do escopo, incluindo `clients/locations.py` e arquivos documentais/testes preexistentes.
- `uv run ty check` — passou: `All checks passed!`
- `uv run pytest --basetemp .pytest-tmp-task6` — passou: `254 passed, 1 warning`.
- `git diff --check` — passou.
- `git status --short` — mostrou somente a alteração preexistente protegida em
  `db/locations.json`, o arquivo não rastreado `../ideas.md` e os documentos desta
  tarefa; nenhum deles foi incluído por `git add`.

O warning do pytest é a depreciação de `httpx` no `starlette.testclient`, sem falha.

## Self-review

O diff foi revisado antes da entrega. Não houve lacuna de código diretamente exigida,
portanto não foram alterados Python, JavaScript, CSS ou dados. A spec já refletia as
visões administrativas e o plano foi atualizado para registrar o estado final e a
limitação do format check global. `ARCHITECTURE.md` não mudou porque as fronteiras
descritas permanecem válidas.

## Arquivos alterados nesta tarefa

- `docs/superpowers/specs/2026-09-09-participantes-e-instituicoes-design.md`
- `docs/superpowers/plans/2026-09-15-participantes-instituicoes-admin.md`
- `.superpowers/sdd/2026-09-15-participantes-instituicoes-admin/task-6-report.md`

## Limitações e achados não resolvidos

O `ruff format --check .` global continua vermelho por arquivos fora do escopo desta
auditoria, já existentes no baseline. Corrigi nenhum deles deliberadamente. O Git não
foi usado para incluir arquivos protegidos.

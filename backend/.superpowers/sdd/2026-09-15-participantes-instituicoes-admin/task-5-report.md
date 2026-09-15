# Relatório da Tarefa 5

## Mini-design visual

- **Job:** administrar catálogos reais no painel autenticado.
- **Artefato:** listas de cards empilháveis, contagem visível, busca e ações CRUD.
- **Dados/interações:** após validar `/auth/users/me/`, `loadAdminData` busca os endpoints
  protegidos; instituições exibem nome/cidade/estado e participantes exibem nome, CPF
  mascarado, e-mail e instituição.
- **Leitura mobile:** cards empilhados, busca em largura total, ações por botões e sem hover.
- **Estados:** lista, vazio, vazio de busca, falha de carga com retry e toast de mutação.
- **Fallback:** erro estruturado da API é comunicado sem detalhes de filesystem; conflito 409
  não altera o estado local.
- **Custo/performance:** HTML build-free, uma carga paralela dos catálogos e filtragem local.
- **QA:** contratos Python/Node e Playwright cobrem shell, autenticação, carga, máscara e
  regressão da programação.

## RED/GREEN

Os três contratos novos foram escritos antes da implementação e falharam: faltavam as duas
seções no shell, `participantRow`/máscara e as funções de catálogo. Depois da implementação,
os mesmos contratos passaram.

## Comandos e saídas

- `uv run pytest tests/test_home_page.py tests/test_home_editor_js.py tests/test_catalog_ui_contract.py`
  — **95 passed**.
- `uv run pytest tests/e2e` — **18 passed**; Chromium estava disponível.
- `uv run ruff check .` — **All checks passed**.
- `uv run ty check` — **All checks passed**.
- `uv run ruff format --check .` — falha em arquivos preexistentes fora do escopo (`clients/locations.py`
  e documentação/fixtures já modificadas); os cinco testes alterados foram formatados diretamente.
- `git diff --check` — sem erros.

## Self-review

O shell inicial continua sem catálogos e PII. Os dados só são carregados depois da identidade,
o CPF completo é usado apenas no formulário pós-auth/payload, e a exclusão de instituição em
uso depende da resposta 409 sem mutação local. A navegação de agenda, locais, eixos,
configurações e seu view state foi preservada.

## Arquivos

Alterados no commit: `static/home/index.html`, `static/home/home.js`, `static/home/home.css`,
`tests/test_home_page.py`, `tests/test_home_editor_js.py`, `tests/test_catalog_ui_contract.py`,
`tests/e2e/conftest.py` e `tests/e2e/test_home_panel.py`.

Preservados fora do commit: `db/locations.json`, `docs/...` já modificados e `../ideas.md`.

## Rodada de correção 1

Consolidei as funções duplicadas, corrigi restauração de foco/cursor nos quatro campos de
busca, tratei falhas de rede em salvar/excluir sem mutar estado, adicionei indicador explícito
de carregamento e retry, escapei IDs de opções e ampliei contratos Node para foco, erro de rede
e markup seguro. As verificações finais registraram 98 testes focados e 18 E2E aprovados.
`ruff check`, `ty check` e `git diff --check` passaram. `ruff format --check .` continua apontando
somente `clients/locations.py`, snippets da documentação/plano e os testes preexistentes que não
foram reformata­dos fora do escopo.

## Rodada de correção 2

Removidas as cinco funções legacy mortas e acrescentado contrato de ausência delas. Testes focados: 98 passed. E2E: 18 passed. Ruff check, ty check e git diff --check passaram. O format check global continua limitado aos arquivos preexistentes fora do escopo, conforme registrado anteriormente.

## Rodada de correção 3 (final)

O harness Node passou a exportar renderizadores, estados e ações. O teste operacional comprova
para instituições e participantes contagem/dados, vazio, sem resultados, loading/erro/retry,
criação/edição/exclusão após 2xx, payload de CPF normalizado, máscara sem CPF completo na linha,
409 de instituição vinculada, 401/rede preservando estado e busca com foco/cursor. Todas as
funções legacy mortas foram removidas.

Resultados reais: testes focados **100 passed**; `tests/e2e` **18 passed**; `ruff check .`,
`ty check` e `git diff --check` passaram. `ruff format --check .` permanece limitado por
arquivos preexistentes fora do escopo (`clients/locations.py`, snippets de docs/plano e testes
não alterados), que não foram reformatados.

## Rodada de correção 4/5

O parecer apontou cobertura operacional assimétrica. Mantive a implementação existente e
acrescentei quatro testes Node executáveis, separados por entidade e por responsabilidade:

- `test_institution_catalog_has_independent_states_and_async_retry`: instituições com
  contagem/dados, vazio, sem resultados e transição controlada loading → erro/retry → nova
  resposta 2xx, confirmando o novo estado carregado.
- `test_participant_catalog_has_independent_states_and_async_retry`: a mesma sequência
  exclusivamente para participantes.
- `test_participant_edit_updates_rendered_state_after_success_and_search_selection`: filtro
  efetivo de participantes, preservação de foco e de `selectionStart`/`selectionEnd`, edição
  real após 2xx, atualização de state/HTML e CPF normalizado no payload mas ausente da linha.
- `test_catalog_save_and_delete_failures_preserve_both_entities_safely`: para cada uma das
  duas entidades, save e delete com 401 e falha de rede; o registro permanece e o feedback é
  seguro. O teste anterior continua cobrindo 409 de instituição vinculada.

RED/GREEN: a primeira execução dos testes novos encontrou apenas limitações do fake DOM e do
fake FormData; após ajustar o harness para observar o container renderizado e fornecer campos
válidos, os quatro casos passaram sem alteração de produção.

Saídas reais desta rodada:

- `uv run pytest tests/test_home_page.py tests/test_home_editor_js.py tests/test_catalog_ui_contract.py -v`
  — **104 passed** nos casos; o processo exibiu ao final o `PermissionError [WinError 5]`
  conhecido do cleanup automático de `pytest-current` no Windows.
- `uv run pytest tests/e2e -v --basetemp .pytest-tmp-round4-e2e` — **18 passed**, exit 0,
  em 31,46s, com 1 warning de depreciação do Starlette/httpx.
- `uv run ruff check .` — **All checks passed!**
- `uv run ruff format --check .` — falha somente nos arquivos preexistentes fora do escopo:
  `clients/locations.py`, o plano/documentação e `tests/test_catalog_ui_contract.py`/o
  harness preexistente; nenhum deles foi reformatado.
- `uv run ty check` — **All checks passed!**
- `git diff --check` — exit 0, sem erros; apenas avisos normais de conversão LF/CRLF nos
  arquivos já modificados.

Arquivos desta rodada: `tests/test_home_editor_js.py` e este relatório. Foram preservados
`db/locations.json`, `docs/...` e `../ideas.md`; não houve alteração de dados, credenciais ou
implementação visual.

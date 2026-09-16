# Relatório da Tarefa 7 — revisão dos contratos de design

## Escopo e método

Revisei `AGENTS.md`, `DESIGN.md`, `ARCHITECTURE.md`, a spec, o briefing e a implementação
atual de `static/home/`. Não reexecutei Tarefas 1–6 como implementação e não despachei
subagents. O checkout iniciou limpo no commit `c5489e9`.

## Contratos mapeados

- A barra lateral contém Programação, Locais, Eixos, Instituições e Participantes; cada item
  usa botão, rótulo visível e SVG decorativo com `aria-hidden="true"`.
- Perfil reúne Configurações e Sair no rodapé; o gatilho e as duas opções mantêm nome visível,
  SVG e foco acessível.
- `.editor-sidebar` usa `--color-surface-subtle`/`--color-text`; itens usam
  `--color-surface`/`--color-border`; ativo usa `--color-surface-selected` e
  `--color-navigation`.
- O foco visível é implementado com `:focus-visible` e `--color-focus` para controles e
  elementos do perfil.
- O layout desktop/tablet/mobile mantém sidebar, reduz largura entre 750–1024px e converte a
  navegação em barra horizontal até 749px; os ícones permanecem no markup em todos os estados.
- `@media (prefers-reduced-motion: reduce)` reduz transições/animações e desativa rolagem suave.

## Desvio encontrado e correção

Os botões “Instituições” e “Participantes” eram os únicos itens da navegação principal sem
SVG. Isso violava o contrato de ícone consistente em todos os itens, estados e viewports.
Adicionei um SVG `sidebar-icon` a cada botão, preservando os tokens e o padrão visual existente.
Atualizei a asserção de contagem de cinco para sete ícones de navegação/perfil de ação e adicionei
um teste de contrato que inspeciona os oito controles da barra lateral, verificando SVG,
`aria-hidden` e classe do ícone.

## TDD — RED/GREEN

RED, antes da alteração de produção:

```text
uv run pytest --basetemp .pytest-tmp-design-review tests/test_home_page.py -k every_sidebar_item_has_a_visible_accessible_svg_icon -q
1 failed, 13 deselected, 1 warning
assert all('class="sidebar-icon"' in item ...)
```

Causa esperada: os fragmentos de Instituições e Participantes não continham
`class="sidebar-icon"`.

GREEN, após a menor correção:

```text
uv run pytest --basetemp .pytest-tmp-design-review tests/test_home_page.py -k "every_sidebar_item_has_a_visible_accessible_svg_icon or editor_navigation_is_sidebar" -q
2 passed, 12 deselected, 1 warning
```

## Arquivos alterados

- `static/home/index.html`: dois SVGs da barra lateral.
- `tests/test_home_page.py`: contrato de ícones e contagem atualizada.
- Este relatório.

`home.js`, `home.css` e os demais testes relacionados não exigiram correção.

## Validações

- `uv run pytest --basetemp .pytest-tmp-design-review tests/test_home_page.py tests/test_home_editor_js.py tests/test_catalog_ui_contract.py -q` — **109 passed**, 1 warning de depreciação do Starlette/httpx.
- `uv run pytest --basetemp .pytest-tmp-design-review-e2e tests/e2e -q` — **limitado pelo baseline**: 1 falha de login porque `users.json` não foi encontrado no diretório temporário e 17 erros de fixture porque o cleanup removeu o diretório `basetemp` durante a execução.
- `uv run ruff check .` — **passou**.
- `uv run ruff format --check .` — **falhou no baseline**: seis arquivos preexistentes fora do escopo continuam não formatados (`clients/locations.py`, plano/spec e testes anteriores, incluindo E2E); o teste alterado foi formatado.
- `uv run ty check` — **passou**.
- `git diff --check` — **passou**, apenas com avisos normais de conversão LF/CRLF.

## Self-review

O diff contém somente os dois arquivos autorizados modificados e este relatório. Não houve
alteração em `.env`, credenciais, usuários, locations, `ideas.md`, dados persistidos,
`home.js`, `home.css` ou arquivos de arquitetura/design. Os ícones usam `currentColor`,
herdam os estados ativo/inativo existentes e não introduzem nova paleta ou token. O contrato
de foco, contraste, responsividade e movimento reduzido permaneceu coberto pela implementação
existente e pelas asserções revisadas.

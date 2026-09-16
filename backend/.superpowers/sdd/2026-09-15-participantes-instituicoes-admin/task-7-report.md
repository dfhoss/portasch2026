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

## Complemento aprovado — ações, buscas e selects

A revisão do código atual confirmou que `.primary-action` dependia de seletores genéricos e que
as quatro buscas não compartilhavam um campo com label visível. Instituições e participantes
renderizavam botões CRUD sem ícones, enquanto os locais já usavam o menu contextual. O formulário
também não tinha um contrato visual próprio para `<select>`.

O complemento padronizou `.primary-action`, `.search-bar`/`.search-field`, os menus CRUD de
`.card-actions` e os controles `.select-control-wrap`/`.select-control`. Instituições,
participantes e locais agora usam o mesmo menu com ícones SVG de editar/excluir, nomes acessíveis,
ordem CRUD e separação semântica da ação destrutiva. O popup mantém o raio somente no contêiner;
os itens internos, inclusive `Excluir`, usam raio zero. O select simples recebe chevron SVG e o
select múltiplo preserva a UI nativa. O nome do landmark de busca usa “Busca de ...”, distinto
do label do campo “Buscar ...”, evitando dois resultados para o mesmo `get_by_label`.

As regras e referências WAI-ARIA/MDN foram registradas em `DESIGN.md`. Não foi criado um
combobox falso: o popup de opções do `<select>` continua sob controle nativo do navegador e do
sistema operacional.

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

Para o contrato autônomo de ação primária e busca compartilhada, o RED foi:

```text
uv run pytest --basetemp .pytest-tmp-design-standardization tests/test_home_page.py tests/test_catalog_ui_contract.py -k "primary_action_owns_its_complete_visual_contract or search_fields_share_accessible_visual_contract_and_design_documentation" -q
2 failed, 67 deselected, 3 warnings
```

Para ações CRUD, popup e selects, o RED foi `2 failed, 54 deselected, 1 warning`. Depois da
implementação, a suíte focada passou com `113 passed, 3 warnings`. A regressão E2E do nome
duplicado do landmark de busca foi corrigida usando nomes distintos para landmark e campo; a
suíte E2E completa passou depois com `19 passed, 1 warning`.

Por solicitação de revisão visual, foi criado ainda um teste RED específico para o raio dos itens
do menu (`1 failed, 55 deselected, 3 warnings`). A correção foi somente aplicar
`border-radius: var(--space-0)` em `.menu-panel .menu-item`; o teste GREEN passou.

Por solicitação adicional, medi os cabeçalhos de Programação, Locais, Eixos, Instituições e
Participantes no navegador. O botão tinha o mesmo contrato próprio em todas as telas (`40px`,
`1px 16px`, raio `8px`, cor `rgb(22, 115, 74)`), mas o bloco de título dos dois catálogos tinha
uma linha extra de contagem. Com `align-items: center`, isso deslocava a ação `13,89px` do topo,
contra `3,39px` nas demais telas. O teste E2E reproduziu o RED; a correção usa
`align-items: flex-start` no `.content-header` e envolve as ações dos catálogos em
`.toolbar-actions`, conforme o contrato documentado. O GREEN confirmou offset superior zero e
igualdade de dimensões, espaçamento, raio, padding e cor nos cinco cabeçalhos.

## Arquivos alterados

- `DESIGN.md`: contratos de ação primária, busca, menus CRUD, selects e alinhamento de cabeçalhos,
  com referências técnicas.
- `static/home/home.css`: contratos autônomos de ações, campos, popup, selects e cabeçalhos.
- `static/home/home.js`: labels de busca, menus CRUD com SVG, estado acessível, selects padronizados
  e contêiner compartilhado das ações dos catálogos.
- `tests/test_home_page.py`: contrato completo de `.primary-action`.
- `tests/test_catalog_ui_contract.py`: contratos de busca, ações, popup, raio zero e selects.
- `tests/e2e/test_home_panel.py`: uso do menu CRUD e pré-condição de catálogo baseada no nome único.
- Este relatório.

`static/home/index.html` não exigiu alteração nesta extensão; os ícones da barra lateral permanecem
os corrigidos na primeira parte da Tarefa 7.

## Validações

- `uv run pytest --basetemp .pytest-tmp-design-final-focused-2 tests/test_home_page.py tests/test_home_editor_js.py tests/test_catalog_ui_contract.py -q` — **113 passed**, 1 warning preexistente.
- `uv run pytest --basetemp .pytest-tmp-design-standardization-e2e-final-serial tests/e2e -q` — **19 passed**, 1 warning preexistente de depreciação do Starlette/httpx.
- `uv run pytest --basetemp .pytest-tmp-primary-alignment-unit-green tests/test_catalog_ui_contract.py -k catalog_headers_share_schedule_toolbar_and_primary_action_structure -q` — **1 passed**.
- `uv run pytest --basetemp .pytest-tmp-primary-alignment-e2e-green tests/e2e/test_home_panel.py::test_schedule_and_catalog_headers_share_action_style_and_content_spacing -q` — **1 passed**.
- `uv run pytest --basetemp .pytest-tmp-full-final-serial -q` — **259 passed, 3 falhas do baseline**:
  os testes de dados esperam `db/participants.json` vazio, mas esse arquivo já estava modificado
  com um participante antes desta execução; ele não foi alterado nem revertido.
- `uv run ruff check .` — **passou**.
- `uv run ruff format --check .` — **falhou no baseline**: sete arquivos continuam não formatados,
  incluindo blocos preexistentes em `clients/locations.py`, plano/spec e testes de contrato/E2E;
  nenhuma regra de produção foi alterada para mascarar essa pendência.
- `uv run ty check` — **passou**.
- `git diff --check` — **passou**, apenas com avisos normais de conversão LF/CRLF.

## Self-review

O diff desta execução contém somente `DESIGN.md`, `static/home/`, os testes de contrato/E2E e este relatório. Não houve
alteração em `.env`, credenciais, usuários, `locations.json`, `ideas.md` ou arquivos de
arquitetura. O `db/participants.json` já estava modificado antes desta extensão e não foi
incluído nem alterado por ela. Os ícones usam `currentColor`, os estados usam tokens semânticos,
os nomes acessíveis são explícitos e os controles preservam foco, contraste, responsividade e
`prefers-reduced-motion`. Os cabeçalhos agora usam a mesma estrutura de ação e não introduzem
espaçamento vertical específico por catálogo.

## Verificação independente e resolução dos itens não verificáveis pela diff

A revisão da tarefa marcou como `⚠️` os contratos mantidos em arquivos inalterados. A inspeção
direta confirmou:

- `static/home/index.html:30-43` mantém rótulos textuais, SVGs decorativos com
  `aria-hidden="true"` e nomes acessíveis para os cinco itens principais, Perfil,
  Configurações e Sair.
- `static/home/home.css:58-71` declara os tokens semânticos; `:112-115` aplica foco visível
  com `--color-focus`; `:173-230` usa superfícies, texto, bordas e estados de navegação
  semânticos; `:235-293` cobre o gatilho e as opções de Perfil com contraste e foco.
- `static/home/home.js:657-664` mantém `aria-current="page"` somente no item ativo, enquanto
  `home.css:226-230` diferencia o estado ativo por superfície e cor além do rótulo.
- `static/home/home.css:1097-1104` respeita `prefers-reduced-motion`; `:1106-1115` mantém
  duas colunas e reduz a barra lateral entre 750px e 1024px; `:1117-1158` converte a
  navegação para uma barra horizontal até 749px sem ocultar os rótulos.
- `tests/test_home_page.py:136-167` verifica a estrutura da barra lateral, os oito controles,
  os SVGs e `aria-hidden`; `tests/e2e/test_home_panel.py:85-124` verifica os breakpoints do
  layout e a ausência de lacuna entre status e conteúdo.

A execução independente das validações originais da Tarefa 7, após o commit do implementador,
produziu:

- contratos UI: `109 passed`, com o warning preexistente de depreciação Starlette/httpx;
- E2E: `19 passed`, com o mesmo warning preexistente;
- `uv run ruff check .`: passou;
- `uv run ty check`: passou;
- `git diff --check`: passou;
- `uv run ruff format --check .`: falhou somente nos sete arquivos que já possuem blocos fora
  do formato (`clients/locations.py`, plano/spec e testes de contrato/E2E); a alteração de
  produção permanece validada por `ruff check`.

A primeira execução E2E relatada pelo implementador encontrou uma corrida de limpeza do
`basetemp`; a repetição independente acima passou integralmente, portanto essa limitação não
permanece como falha da implementação. Nenhum ajuste adicional de código foi necessário nessa
execução original; o complemento descrito acima foi implementado posteriormente a partir da
revisão aprovada dos contratos de design.

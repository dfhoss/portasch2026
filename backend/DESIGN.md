# Sistema de design administrativo

## Objetivo

Este documento é a fonte oficial da identidade visual da interface administrativa do Portas
Abertas em `static/admin/`. Leia-o antes de criar ou alterar qualquer elemento da UI.

A interface deve transmitir uma sensação institucional, calma, clara e confiável. Ela usa verde
escuro para ancorar a navegação, verde mais vivo para ações, superfícies em branco quente e cores
de feedback discretas. Priorize hierarquia, legibilidade e conclusão das tarefas em vez de efeitos
decorativos.

## Modelo de tokens

Os tokens têm duas camadas:

- **Tokens primitivos** descrevem a paleta e as escalas disponíveis. Não os use diretamente nas
  regras de componentes quando houver um token semântico para a função pretendida.
- **Tokens semânticos** descrevem a finalidade, como texto, superfície, borda ou ação. Os
  componentes devem consumi-los para que a identidade visual possa mudar sem reescrever seletores.

Use nomes em kebab-case minúsculo. Defina tokens globais em `:root` e consuma-os com
`var(--token-name)`. Não duplique um valor literal apenas para criar um nome específico de
componente.

## Tokens CSS

O bloco a seguir é canônico. Mantenha as declarações correspondentes em `admin.css` alinhadas a
ele ao implementar ou alterar a interface.

```css
:root {
  color-scheme: light;

  /* Cores primitivas */
  --green-50: #f5faf7;
  --green-100: #e5f1eb;
  --green-200: #cfe3d8;
  --green-300: #91b5a2;
  --green-500: #2c614a;
  --green-600: #16734a;
  --green-700: #173c2d;
  --green-800: #203e31;
  --neutral-0: #ffffff;
  --neutral-50: #fafbfa;
  --neutral-100: #f3f5f2;
  --neutral-200: #e1e6e3;
  --neutral-300: #d8dfdb;
  --neutral-400: #bac5bf;
  --neutral-600: #67746d;
  --neutral-800: #24312a;
  --yellow-50: #fff8d9;
  --yellow-400: #ead27b;
  --red-100: #fce8e8;
  --red-600: #aa2f2f;
  --red-800: #7f1d1d;
  --overlay-green: #17251f88;

  /* Tipografia */
  --font-family-sans: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-md: 1rem;
  --font-size-lg: 1.25rem;
  --font-size-xl: 1.5rem;
  --font-size-2xl: 2rem;
  --font-weight-regular: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
  --line-height-tight: 1.2;
  --line-height-normal: 1.5;

  /* Espaçamento */
  --space-0: 0;
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;

  /* Forma, bordas e elevação */
  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-pill: 999px;
  --border-width: 1px;
  --shadow-dialog: 0 1rem 3rem rgb(23 60 45 / 24%);
  --shadow-card: 0 0.5rem 1.5rem rgb(23 60 45 / 8%);

  /* Movimento */
  --duration-fast: 120ms;
  --duration-normal: 200ms;
  --ease-standard: ease-out;

  /* Cores semânticas */
  --color-page: var(--neutral-100);
  --color-surface: var(--neutral-0);
  --color-surface-subtle: var(--neutral-50);
  --color-surface-selected: var(--green-100);
  --color-text: var(--neutral-800);
  --color-text-muted: var(--neutral-600);
  --color-text-on-dark: var(--neutral-0);
  --color-border: var(--neutral-300);
  --color-border-strong: var(--neutral-400);
  --color-action-primary: var(--green-600);
  --color-action-primary-hover: var(--green-500);
  --color-navigation: var(--green-700);
  --color-navigation-active: var(--green-500);
  --color-focus: var(--green-300);
  --color-danger: var(--red-600);
  --color-danger-surface: var(--red-100);
  --color-danger-text: var(--red-800);
  --color-warning-surface: var(--yellow-50);
  --color-warning-border: var(--yellow-400);
  --color-backdrop: var(--overlay-green);

  /* Layout semântico */
  --sidebar-width: 13.75rem;
  --content-width: 75rem;
  --control-height: 2.5rem;
  --content-padding: var(--space-8);
  --panel-padding: var(--space-4);
  --component-gap: var(--space-3);
}
```

## Regras de uso

### Componentes

- Variantes semânticas como `.primary-action` e `.danger-action` carregam seu contrato visual
  completo (espaçamento, borda, raio, superfície e tipografia), independentemente do contêiner.

### Cor

- Use `--color-navigation` apenas para navegação persistente ou âncoras de marca igualmente fortes.
- Use `--color-action-primary` para a única ação primária de um contexto. Ações secundárias usam
  tokens de superfície, texto e borda em vez de outro preenchimento saturado.
- Use `--color-danger` para ações destrutivas e erros, nunca para ênfase comum.
- Use tokens semânticos de texto e superfície, em vez de cores primitivas, nos seletores de
  componentes.
- Não comunique o estado somente pela cor; combine-a com texto, ícone ou ambos.

### Tipografia

- Use a pilha de fontes do sistema; o painel não deve depender do download de uma fonte para
  continuar utilizável.
- Títulos de página usam `--font-size-xl` e `--font-weight-bold`. Títulos de seção usam
  `--font-size-lg` e `--font-weight-semibold`. O texto corrido usa `--font-size-sm` ou
  `--font-size-md` com `--line-height-normal`.
- Evite texto corrido em caixa alta. A caixa alta fica reservada para rótulos curtos e eyebrows.

### Espaçamento e layout

- Use a escala de espaçamento em vez de valores arbitrários em pixels. Adicione um token primitivo
  somente quando uma necessidade recorrente não puder ser representada pela escala existente.
- Mantenha o conteúdo principal em `--content-width` ou abaixo dele; permita que tabelas densas
  rolem em vez de reduzir o texto abaixo de `--font-size-sm`.
- Em larguras de desktop acima de 1024px, use áreas explícitas de grid `sidebar`, `message` e
  `content`. O conteúdo deve seguir imediatamente a mensagem de status; a altura da barra lateral
  não deve criar uma linha vazia implícita acima dele.
- Entre 750px e 1024px, mantenha o layout de duas colunas, mas reduza a barra lateral para `12rem`
  e o padding do conteúdo para `--space-6`.
- Em 749px ou menos, converta a barra lateral em navegação horizontal, empilhe os formulários e
  mantenha as ações primárias visíveis. Não dependa de hover para dar acesso às ações.
- A barra lateral administrativa usa `--color-surface-subtle` com `--color-text`. Itens de
  navegação usam `--color-surface` e `--color-border` para uma borda sutil em repouso; reserve
  `--color-surface-selected` e `--color-navigation` para o item ativo e sua ênfase, evitando uma
  barra lateral totalmente verde saturada.
- Os itens da barra lateral usam um ícone consistente ao lado de cada rótulo, e a ação “Sair” é o
  último item da lista de navegação, com o mesmo tratamento de foco acessível e contraste.
- A edição e a data do evento pertencem a “Configurações”, não ao espaço de trabalho da
  programação. Rotule a edição como “Edição do evento” para deixar sua finalidade explícita; salve-a
  pelo mesmo fluxo de persistência da agenda.
- Os locais são organizados por grupos explícitos armazenados em `locations.json`. Um grupo tem
  nome e uma categoria (`blocos`, `laboratorios`, `estacionamentos` ou `outros`); cada sala pertence
  a um grupo por meio de `groupId` e armazena `roomNumber` e `description`. A página de locais
  exibe grupos como accordions (`Bloco A`, `LAB 01` etc.) e suas salas; “Estacionamentos” também é
  um accordion que contém diretamente seus locais de estacionamento, sem grupo aninhado. Use o
  mesmo token de espaçamento entre todos os grupos, independentemente da categoria. Os nomes das
  salas continuam sendo as referências da agenda.
- Uma sessão da agenda armazena `locations` como lista. Várias salas podem compartilhar um horário;
  salas com horários diferentes usam entradas de sessão separadas para a mesma atividade. A entrada
  legada `location` é aceita somente para migração ao formato de lista.
- Todo `.content-header` no nível da página usa `--space-5` abaixo dele. Ações primárias do
  cabeçalho pertencem a `.toolbar-actions` para que as telas de agenda e catálogo compartilhem
  dimensões e alinhamento.
- O espaço de trabalho da programação mantém uma única ação de criação no cabeçalho da página:
  `Adicionar seção` é representado por um botão compacto em formato de pílula, com ícone de mais e
  texto visível, ao final da lista de seções, com nome acessível `Adicionar seção`. O shell e o
  estado carregado usam o mesmo ícone SVG, centralizado com o rótulo visível e sem margem extra.
  Sua tipografia deve corresponder às outras pílulas de seção: `--font-size-sm` e
  `--font-weight-regular`. A criação de grupo e atividade pertence ao menu contextual `Adicionar`
  da seção selecionada. A ação primária de salvamento é `Salvar alterações`, desabilitada quando o
  rascunho corresponde à agenda carregada, com status visível `Salvo`/`Alterações não salvas`.
- Para manter o alinhamento do botão `section-add-button` em diferentes níveis de zoom, use
  `inline-grid` com colunas explícitas e uma caixa `.section-add-icon` centralizada por
  `place-items: center`. Não corrija o alinhamento com deslocamentos manuais em pixels ou
  dependência de baseline/`vertical-align`.

### Componentes e interação

- Controles interativos devem ter um tratamento visível de `:focus-visible` usando `--color-focus`.
- Botões e campos devem ter pelo menos a altura `--control-height`. Os rótulos permanecem visíveis;
  placeholders não substituem rótulos.
- Cards e painéis usam `--color-surface`, `--color-border` e `--radius-lg`. Reserve sombras para
  overlays ou casos em que uma borda não consiga comunicar o limite.
- Todo menu popup ou dropdown compartilha o componente `.menu`, com `.menu-trigger`, `.menu-panel`
  e `.menu-item`; classes de contexto podem existir apenas para posicionamento. O gatilho deve
  ter rótulo acessível, ícone SVG adequado ao tipo de ação e chevron SVG para indicar abertura,
  nunca um caractere ASCII. Dropdowns com múltiplas opções de criação, como `Adicionar` na seção,
  usam somente o chevron no gatilho; o ícone da ação fica nas opções internas. O painel deve ser
  vertical, clicável, ter fundo opaco `--color-surface`, borda
  `--border-width`/`--color-border`, raio `--radius-md`, sombra `--shadow-dialog` e camada acima
  dos cards adjacentes; menus contextuais devem abrir para cima quando houver espaço.
- Em cada momento, mantenha no máximo um menu popup aberto dentro do editor: abrir qualquer
  outro gatilho, inclusive um dropdown da barra, fecha o menu anterior; clicar fora ou executar
  uma opção também fecha o menu atual. Essa regra deve ser implementada no comportamento
  compartilhado de `.menu`, não em regras isoladas de cada contexto.
- Toda opção de um menu deve usar `.menu-item`, ter um ícone SVG acompanhando o rótulo e foco
  visível. O painel com `role="menu"` não tem padding superior ou inferior (`padding-block: 0`);
  cada item define sua própria altura mínima, espaçamento e área clicável. Os itens não têm
  borda própria; a borda pertence somente ao painel do menu. O ícone de `+` fica reservado para
  a criação principal; opções contextuais como grupo e atividade usam ícones específicos. Para
  grupo de atividades, use coleção/camadas, nunca pessoas ou usuários, pois o grupo não representa
  participantes.
- Grupos de atividades devem deixar claro que são expansíveis: o botão `.group-toggle` informa
  `aria-expanded`, usa somente um chevron que acompanha a mudança de estado e tem um rótulo
  acessível contextual como “Abrir grupo X” ou “Fechar grupo X”. Não exiba “Expandir”/“Recolher”
  como texto auxiliar: essa terminologia é abstrata e adiciona ruído ao cabeçalho. A expansão não
  pode depender de hover. O `.schedule-group` deve manter `overflow: visible`, pois o painel do
  menu precisa escapar do card e permanecer em primeiro plano. Feche os cantos aplicando raios
  específicos ao `.group-header` — todos os cantos quando recolhido e somente os superiores quando
  expandido — e ao `.group-body`, sem recortar o popup. O `.group-header` deve
  usar uma grid com a coluna flexível do grupo e a coluna automática do menu, mantendo o dropdown
  alinhado ao centro do cabeçalho em diferentes larguras e níveis de zoom. O
  `.group-toggle-indicator` deve ter a mesma caixa explícita de `1.15rem` do `.action-icon`,
  `line-height: 0` e centralizar o SVG como `display: block` dentro dela. O título e o eixo devem
  ficar juntos em `.group-toggle-copy`, enquanto o indicador deve ser um segundo item explícito de
  um layout flexível centralizado; não dependa do auto-placement de uma grid com três filhos.
- O `.menu-chevron` deve seguir o mesmo contrato: caixa explícita de `1.15rem`, `display: grid`,
  `place-items: center`, `line-height: 0` e SVG como `display: block`. Se o resultado visual de um
  ajuste não corresponder ao pedido, não acumule tentativas empíricas: pesquise referências
  técnicas confiáveis e registre a solução baseada nessa pesquisa.
- Diálogos precisam de título claro, gerenciamento de foco pelo teclado e uma ação primária
  explícita com o rótulo “Salvar” no canto inferior direito do rodapé. “Salvar” deve compartilhar
  o contrato completo de botão primário com as demais ações primárias: `--control-height`, tokens
  de espaçamento, borda, raio e cores semânticas de ação. Não renderize um botão “Fechar”; o
  backdrop e `Esc` fecham o diálogo. Em diálogos de atividade, coloque “Adicionar horário” à
  esquerda no mesmo rodapé. Ações destrutivas devem ficar visualmente separadas das ações de
  confirmação.
- Oculte a aparência da barra de rolagem na página e nos diálogos sem desabilitar a rolagem;
  preserve a rolagem por teclado, mouse e toque.
- O movimento deve ser breve e informativo. Respeite `prefers-reduced-motion` para transições e
  animações não essenciais.
- Preserve a tela administrativa ativa, a seção selecionada da agenda, os grupos expandidos e a
  posição de rolagem entre recarregamentos usando `sessionStorage`. Valide IDs restaurados contra
  os dados atuais da API, nunca persista conteúdo não salvo de formulários e limpe o estado da tela
  ao sair.

### Hierarquia CRUD e ações contextuais

- Cada contexto deve ter uma única ação primária de criação: use um botão visível com verbo e
  entidade, como `Adicionar local` ou `Adicionar eixo`. Na programação, `Adicionar seção` é o
  botão compacto com `+` ao final da lista; criação de grupo e atividade fica no menu contextual
  `Adicionar` da seção selecionada.
- `Editar` é uma ação secundária contextual. Em seções, grupos, atividades, locais e eixos,
  deve ficar no menu de três pontos do próprio registro, com ícone de lápis e rótulo explícito.
  Não exiba editar como botão paralelo à ação de excluir em cards ou cabeçalhos.
- `Excluir` é sempre a última opção do menu, com ícone de lixeira, separação visual das ações
  comuns e `--color-danger`. A cor nunca é o único sinal: o rótulo deve começar com `Excluir`
  e a confirmação deve identificar o registro e o conteúdo afetado.
- A confirmação é obrigatória quando a exclusão não puder ser facilmente desfeita ou recriada;
  o título e o botão devem descrever o resultado (`Excluir seção`, não `Sim` ou `Tem certeza?`).
  Depois de uma exclusão local no rascunho, informe o estado ao usuário e mantenha a alteração
  pendente até `Salvar alterações`.
- Em menus e toolbars, agrupe ações relacionadas, mantenha a ação primária mais proeminente e
  reduza ações secundárias para evitar excesso de escolha. Os menus devem continuar disponíveis
  por teclado, toque e foco visível em todos os viewports.
- Edição do evento e data do evento pertencem a `Configurações`: são campos de configuração,
  não ações da programação. O mesmo fluxo de persistência usa `Salvar alterações`, cujo estado
  indica `Salvo` ou `Alterações não salvas`; adicionar, editar e excluir no editor altera apenas
  o rascunho até essa confirmação explícita.

## Exemplo

```css
.primary-action {
  min-height: var(--control-height);
  padding-inline: var(--space-4);
  border: var(--border-width) solid var(--color-action-primary);
  border-radius: var(--radius-md);
  background: var(--color-action-primary);
  color: var(--color-text-on-dark);
  transition: background-color var(--duration-fast) var(--ease-standard);
}

.primary-action:hover {
  background: var(--color-action-primary-hover);
}

.primary-action:focus-visible {
  outline: 3px solid var(--color-focus);
  outline-offset: 2px;
}
```

## Alteração do sistema

Antes de adicionar um token, procure um token existente com a mesma finalidade visual. Adicione um
token primitivo somente para uma escala reutilizável e um token semântico somente para uma função
estável da UI. Ao alterar um token canônico, atualize este documento e a declaração CSS juntos;
depois inspecione o login, a navegação, o editor da agenda, as telas de catálogo, os diálogos, os
estados de foco e o layout móvel.

## Referências

- [Material Design — botões](https://m2.material.io/go/design-buttons/) — hierarquia com uma
  única ação de maior destaque e ações secundárias com menor ênfase.
- [Material Design — diálogos](https://m2.material.io/develop/web/components/dialogs) — ações de
  confirmação e cancelamento explícitas, com no máximo duas ações no diálogo.
- [Fluent 2 — botões](https://fluent2.microsoft.design/components/web/react/core/button/usage) —
  uma única ação primária por contexto, rótulos iniciados por verbos e ícones familiares.
- [Fluent 2 — toolbar](https://fluent2.microsoft.design/components/web/react/core/toolbar/usage) —
  ações destrutivas agrupadas e ícones acompanhados de rótulos acessíveis.
- [Carbon Design System — ações comuns](https://carbondesignsystem.com/patterns/common-actions/)
  — exclusão de baixo impacto pode ser imediata; exclusão de maior impacto deve explicar as
  consequências e pedir confirmação.
- [GOV.UK Design System — botões](https://design-system.service.gov.uk/components/button/) —
  ações destrutivas devem ser usadas com parcimônia, com texto explícito e confirmação adicional.
- [Especificação de propriedades personalizadas CSS da W3C](https://www.w3.org/TR/css-variables-1/)
- [Formato do Design Tokens Community Group](https://www.designtokens.org/tr/drafts/format/)
- [MDN: Uso de propriedades personalizadas CSS](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Cascading_variables/Using_custom_properties)
- [web.dev: Renderização precisa com `devicePixelContentBox`](https://web.dev/articles/device-pixel-content-box)
  — explica subpixels, `devicePixelRatio`, zoom e pixel snapping.
- [W3C: CSS Inline Layout](https://www.w3.org/TR/css-inline-3/) — documenta baseline e alinhamento
  vertical de elementos inline e SVG.
- [MDN: Flexbox](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Flexbox)
  — referência para centralização no eixo transversal com `align-items`.
- [MDN: `overflow`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/overflow)
  — diferencia conteúdo visível de conteúdo recortado e explica por que um popup não pode escapar
  de um ancestral com `overflow: hidden`.
- [W3C: CSS Overflow Module Level 3](https://www.w3.org/TR/css-overflow/)
  — especifica o recorte e a relação entre overflow e regiões arredondadas.
- [MDN: `vertical-align`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/vertical-align)
  — documenta o alinhamento por baseline de elementos inline e por que ele não deve ser implícito
  para esse SVG.
- [MDN: `alignment-baseline` em SVG](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Attribute/alignment-baseline)
  — referência para o comportamento de baseline e alinhamento de objetos SVG.

# Sistema de design do frontend

## Escopo e fonte de verdade

Este é o único documento de design do frontend UFFS de Portas Abertas. Reúne a identidade
implementada, decisões de interação, referências históricas e pendências futuras.
A identidade do painel administrativo não substitui a identidade pública.

O runtime carrega, nesta ordem, [fonts.css](static/css/fonts.css),
[tokens.css](static/css/tokens.css), [main.css](static/css/main.css) e
[schedule.css](static/css/schedule.css). Tokens CSS são a fonte executável de cores, famílias
e medidas; as duas folhas de componentes os consomem. Não duplicar paletas por componente.

O modo `standard` usa a identidade normal atual. `high-contrast` e `dark` são aliases
provisórios da paleta legada, centralizados em `tokens.css`. A identidade oficial nova de alto
contraste ainda não foi recebida; não há novo botão de troca nem recoloração dos banners.

## Cores e superfícies

O fundo geral é **`#f1f2ec`**, um off-white levemente acinzentado. Ele substitui o verde
`#d2decf` usado inicialmente nesta integração: é mais claro, mantendo separação dos cartões
brancos (`#ffffff`) um pouco maior que o fundo antigo `#f8f8f0`.
É um neutro funcional da interface, não uma alteração das nove cores oficiais.

A paleta visual de referência está em [Palette.png](static/assets/images/Palette.png). Seus valores
primitivos, mantidos neste documento e em `tokens.css`, permanecem:

| Token | Nome | HEX |
| --- | --- | --- |
| `--palette-magenta` | Magenta | `#ed53c5` |
| `--palette-violet` | Azul-violeta | `#393aed` |
| `--palette-green-bright` | Verde vivo | `#14d204` |
| `--palette-pink` | Rosa claro | `#fda2e3` |
| `--palette-sage` | Verde acinzentado | `#d2decf` |
| `--palette-indigo` | Índigo | `#393cb3` |
| `--palette-green` | Verde | `#368a2e` |
| `--palette-lime` | Verde-limão | `#d8f93b` |
| `--palette-violet-electric` | Violeta elétrico | `#352aff` |

Usar pares semânticos: `action-surface/text`, `selected-surface/text`, `tag-surface/text`,
`status-live-surface/text`, `status-soon-surface/text` e `finalized-*`.
Texto principal é `#171725`, secundário `#42434d`; títulos e ações usam violeta,
bordas e links usam índigo. Tags e estados finalizados/desabilitados usam lavanda clara `#e9e7ff`,
sem reutilizar o verde acinzentado do fundo histórico.
Não usar `brand` como cor universal de texto sobre qualquer fundo.

Cores, bordas, sombras, foco, seleção de texto e pseudo-elementos consomem tokens.
SVG monocromático usa `currentColor`, preservando `fill="none"` quando necessário.
Imagens mantêm suas cores próprias: não aplicar `filter: invert()`.
Estados devem incluir texto, atributos ou contornos, sem depender apenas da cor.

## Tipografia

As sete faces de runtime estão em `static/assets/fonts/`, com URLs relativas, fallback
e `font-display: swap`. O arquivo histórico não é dependência de runtime.

| Papel | Família | Faces disponíveis |
| --- | --- | --- |
| Corpo e agenda | Open Sans | 400 e 700 |
| Títulos e rótulos monoespaçados | Disket Mono | 400 e 700 |
| Detalhes pixelados | Retropix | 400 |
| Informações auxiliares | Garet | 400 e 700 |

Não solicitar peso 900 sintético. Corpo usa referência de 1rem, texto pequeno 0,875rem,
entrelinha de corpo 1,5 e de títulos 1,2; títulos usam `clamp()`.
A troca de tema não muda famílias, pesos, tamanhos ou hierarquia.
Texto longo permanece em caixa de frase. A tipografia embutida nas imagens é rasterizada;
não inferir uma família da aparência da data/horário.

## Medidas e layout

- Conteúdo e banner centralizados com máximo de 1100px.
- Conteúdo: eixo horizontal alinhado ao banner, com largura máxima de 1100px; padding vertical de
  48px 0 80px; até 600px, 32px 16px 60px.
- Cartões: raio de 16px, borda de 2px, padding aproximado de 22px, altura mínima de 260px
  (240px até 600px); texto deve poder ampliar sem corte.
- Controles: 44px no desktop, 38px até 600px.
- Trilho: gap de 20px compartilhado entre CSS e JavaScript.
- Viewport do carrossel: padding interno de 4px em todos os lados para separar as bordas dos
  cartões da máscara de recorte sem alterar o gap de 20px do trilho.
- Espaçamento entre blocos e novos títulos: 32px; manter esse intervalo entre as imagens da
  programação e o título do regulamento.

## Componentes

### Banner / hero

O banner fica centralizado, com largura máxima de `1100px` e margens laterais automáticas.
Ele acompanha o zoom até o limite da largura disponível; em telas menores, ocupa 100% dela.
A arte permanece integral, sem altura fixa, `cover` ou corte. A imagem
desktop é `static/assets/images/hero-desktop.jpg` (5938×1250); até 600px o `picture` seleciona
`hero-mobile.png` (1080×437). Ambas usam `width: 100%`, `height: auto` e `display: block`.
O `h1` continua semanticamente disponível com a classe `visually-hidden`; a arte informa campus,
data e horário pelo `alt`.

### Cartão de atividade

Cada cartão apresenta, nesta ordem: status (`AO VIVO` ou `EM BREVE`), horário, título, local,
descrição e tag. O cartão cresce para preencher a altura da faixa e não deve esconder o texto por
causa de um título mais longo. O hover pode elevar o cartão apenas como reforço secundário; o
estado precisa continuar compreensível sem apontador.

Os cabeçalhos dos cartões de regulamento alinham o número e o título pela baseline tipográfica
(`align-items: baseline`). O número usa `inline-block`, `line-height` explícito e padding próprio;
não trocar por `inline-flex` nem por alinhamento vertical baseado apenas no topo ou no centro,
porque as métricas de fonte e o arredondamento de pixels podem expor desalinhamentos em níveis de
zoom diferentes. Ao ajustar esse componente, conferir a baseline em zoom normal e fracionado.

### Carrossel

O carrossel é uma região rotulada com botões anterior/próximo, indicadores em `role="group"` e
suporte às setas esquerda/direita. O número de cartões visíveis acompanha os breakpoints:

| Largura | Cartões visíveis | Tratamento |
| --- | ---: | --- |
| acima de `900px` | 3 | faixa ampla com controles laterais |
| `601px`–`900px` | 2 | cartões mais largos e dois itens por página |
| até `600px` | 1 | cartão único e controles reduzidos |

Controles, teclado, swipe e autoplay avançam pelas mesmas páginas. A última página alinha ao
último cartão, podendo repetir parte da anterior. Os indicadores têm círculo visual de 12px, sem
escala fracionada; o ativo tem contorno e `aria-current="true"`, além da cor, e o foco tem anel
próprio.

Os indicadores mantêm círculo visual de 12px, mas cada botão oferece área de toque de 48×48px,
seguindo a recomendação de alvos de interação do Material 3. Os alvos dos dots têm gap de 4px e
ficam 8px abaixo da faixa do carrossel; reduzir o espaçamento visual não reduz a área de toque.
As setas também mantêm 48×48px no celular. Cards e grupos da agenda usam o tratamento
outlined/filled sem sombras por padrão; o estado de interação é comunicado pela borda, pela
superfície selecionada ou pelo foco visível.

A passagem entre última e primeira página continua no sentido da navegação, usando cópias
visuais com `aria-hidden` e `inert`. Após a transição, o trilho volta à posição equivalente sem
animação perceptível. Os controles permanecem disponíveis nos dois extremos; só são desabilitados
quando todos os cartões cabem em uma página. Movimento reduzido torna a troca imediata, mantendo
o autoplay existente de 5s. Resize preserva uma página próxima e o foco do indicador após 150ms.

A duração da transição é proporcional à distância percorrida. O retorno contínuo pelas cópias do
trilho pode atravessar mais cartões que uma página normal, mas deve manter a mesma velocidade
visual; o reposicionamento final continua instantâneo e invisível.

## Responsividade, conteúdo e acessibilidade

Preservar `lang="pt-BR"`, landmarks, headings, nomes acessíveis e foco visível.
Conferir 390px, 768px e 1440px, zoom, teclado e toque, sem rolagem horizontal da página.
A troca de tema deve preservar filtros, grupos abertos, foco e posição do carrossel.

Em dispositivos de toque, o feedback nativo retangular do navegador não deve escapar do
formato dos controles arredondados (por exemplo, as pills de “Turno” e “Eixo”). Botões, links e
controles com `role="button"` usam `-webkit-tap-highlight-color: transparent` para evitar esse
overlay sobre o bounding box; o estado pressionado continua sendo comunicado pelo próprio
componente. Essa regra não remove o foco de teclado: `:focus-visible` deve manter seu anel de
foco visível e distinto do feedback de toque.

O hero apresenta Campus Chapecó, “27 de outubro” e “08h30 às 21h”; seu `alt` comunica essas
informações sem repetir o título do `h1`. Não inferir ano ou alterar agenda a partir da arte.
Os assets atualmente usados pela home são o JPG desktop e o PNG móvel descritos acima. Preservar
bytes dos assets, suas proporções e caminhos locais.

A agenda, eixos e locais vêm diretamente dos JSONs em `backend/db/`; não manter cópia local.
Na falha de rede, preservar o conteúdo estático e a interação existentes.
“Ao vivo”, “Em breve” e “Finalizada” precisam de rótulos textuais, além das cores.
Novas animações devem respeitar movimento reduzido. O autoplay existente não pausa em hover/foco;
mudar essa política exige decisão explícita de acessibilidade.

## Matriz de troca e placeholders de alto contraste

Cada linha é uma decisão a preencher quando a identidade chegar. Os identificadores
`PENDENTE_HC_*` são **marcadores de documentação, não valores CSS válidos**.
Nenhuma célula pendente autoriza reaproveitar automaticamente o tema escuro atual ou o antigo.

| Token semântico | Normal implementado | Alto contraste a receber | Consumidor / finalidade |
| --- | --- | --- | --- |
| `--color-page` | `#f1f2ec` | `PENDENTE_HC_PAGE` | body; fundo geral |
| `--color-surface` | `#ffffff` | `PENDENTE_HC_SURFACE` | Cartões, agenda, detalhes e regulamento; neutro funcional adicional |
| `--color-brand` | `var(--palette-violet)` | `PENDENTE_HC_BRAND` | Títulos e referência de marca |
| `--color-brand-soft` | `var(--palette-indigo)` | `PENDENTE_HC_BRAND_SOFT` | Ênfase secundária / compatibilidade; não significa transparência |
| `--color-accent` | `var(--palette-lime)` | `PENDENTE_HC_ACCENT` | Destaques |
| `--color-accent-line` | `var(--palette-lime)` | `PENDENTE_HC_ACCENT_LINE` | Separadores decorativos |
| `--color-live` | `var(--palette-magenta)` | `PENDENTE_HC_LIVE` | Indicador ao vivo; acompanhado de texto |
| `--color-text` | `#171725` | `PENDENTE_HC_TEXT` | Texto principal; neutro funcional adicional |
| `--color-text-muted` | `#42434d` | `PENDENTE_HC_TEXT_MUTED` | Texto secundário; neutro funcional adicional |
| `--color-tag-surface` | `var(--palette-sage)` | `PENDENTE_HC_TAG_SURFACE` | Tags e contagens |
| `--color-tag-text` | `var(--palette-indigo)` | `PENDENTE_HC_TAG_TEXT` | Texto sobre tags |
| `--color-border` | `var(--palette-indigo)` | `PENDENTE_HC_BORDER` | Limites funcionais |
| `--color-border-hover` | `var(--palette-violet)` | `PENDENTE_HC_BORDER_HOVER` | Hover de cartões/controles |
| `--color-focus` | `var(--palette-violet)` | `PENDENTE_HC_FOCUS` | Anel de foco sobre superfícies claras |
| `--color-focus-ring` | `var(--palette-lime)` | `PENDENTE_HC_FOCUS_RING` | Camada externa de foco sobre áreas escuras |
| `--color-card-shadow` | `rgb(57 60 179 / 8%)` | `PENDENTE_HC_CARD_SHADOW` | Sombra normal, derivada do índigo |
| `--color-card-shadow-hover` | `rgb(57 60 179 / 14%)` | `PENDENTE_HC_CARD_SHADOW_HOVER` | Sombra elevada |
| `--color-finalized-surface` | `var(--palette-sage)` | `PENDENTE_HC_FINALIZED_SURFACE` | Atividade finalizada |
| `--color-finalized-text` | `#42434d` | `PENDENTE_HC_FINALIZED_TEXT` | Texto de atividade finalizada |
| `--color-finalized-border` | `var(--palette-indigo)` | `PENDENTE_HC_FINALIZED_BORDER` | Borda de atividade finalizada |
| `--color-finalized-badge` | `var(--palette-indigo)` | `PENDENTE_HC_FINALIZED_BADGE` | Fundo do rótulo finalizado |
| `--color-finalized-badge-text` | `#ffffff` | `PENDENTE_HC_FINALIZED_BADGE_TEXT` | Texto do rótulo finalizado |
| `--color-hero-surface` | `var(--palette-lime)` | `PENDENTE_HC_HERO_SURFACE` | Fundo semântico do banner |
| `--color-hero-text` | `var(--palette-violet)` | `PENDENTE_HC_HERO_TEXT` | Texto HTML equivalente à marca |
| `--color-hero-grid` | `rgb(255 255 255 / 55%)` | `PENDENTE_HC_HERO_GRID` | Grade decorativa proposta; opacidade não extraída do PNG |
| `--color-badge-surface` | `var(--palette-violet)` | `PENDENTE_HC_BADGE_SURFACE` | Faixa UFFS DE |
| `--color-badge-text` | `var(--palette-lime)` | `PENDENTE_HC_BADGE_TEXT` | Texto UFFS DE |
| `--color-action-surface` | `var(--palette-violet)` | `PENDENTE_HC_ACTION_SURFACE` | Botão principal / controle de carrossel |
| `--color-action-text` | `var(--palette-lime)` | `PENDENTE_HC_ACTION_TEXT` | Texto do botão principal |
| `--color-action-hover` | `var(--palette-indigo)` | `PENDENTE_HC_ACTION_HOVER` | Hover de ação |
| `--color-selected-surface` | `var(--palette-violet)` | `PENDENTE_HC_SELECTED_SURFACE` | Visão selecionada da agenda / indicador ativo |
| `--color-selected-text` | `var(--palette-lime)` | `PENDENTE_HC_SELECTED_TEXT` | Texto de seleção |
| `--color-link` | `var(--palette-indigo)` | `PENDENTE_HC_LINK` | Links em superfície clara |
| `--color-link-hover` | `var(--palette-violet)` | `PENDENTE_HC_LINK_HOVER` | Hover de link |
| `--color-status-live-surface` | `var(--palette-magenta)` | `PENDENTE_HC_STATUS_LIVE_SURFACE` | Badge AO VIVO |
| `--color-status-live-text` | `#171725` | `PENDENTE_HC_STATUS_LIVE_TEXT` | Texto escuro sobre magenta |
| `--color-status-soon-surface` | `var(--palette-lime)` | `PENDENTE_HC_STATUS_SOON_SURFACE` | Badge EM BREVE |
| `--color-status-soon-text` | `var(--palette-indigo)` | `PENDENTE_HC_STATUS_SOON_TEXT` | Texto sobre limão |
| `--color-disabled-surface` | `var(--palette-sage)` | `PENDENTE_HC_DISABLED_SURFACE` | Controle indisponível |
| `--color-disabled-text` | `#42434d` | `PENDENTE_HC_DISABLED_TEXT` | Texto indisponível com semântica disabled |
| `--color-field-surface` | `#ffffff` | `PENDENTE_HC_FIELD_SURFACE` | Campos futuros, se necessários |
| `--color-field-text` | `#171725` | `PENDENTE_HC_FIELD_TEXT` | Texto de entrada |
| `--color-placeholder` | `#42434d` | `PENDENTE_HC_PLACEHOLDER` | Placeholder de entrada |
| `--color-selection-surface` | `var(--palette-indigo)` | `PENDENTE_HC_SELECTION_SURFACE` | Seleção de texto |
| `--color-selection-text` | `#ffffff` | `PENDENTE_HC_SELECTION_TEXT` | Texto selecionado |

### Área reservada à identidade de alto contraste

| Informação | Placeholder |
| --- | --- |
| Arquivos oficiais e data de recebimento | `PENDENTE_HC_FONTES_OFICIAIS` |
| Paleta primitiva e valores HEX | `PENDENTE_HC_PALETA` |
| Banner horizontal | `PENDENTE_HC_BANNER_HORIZONTAL` |
| Banner compacto / móvel | `PENDENTE_HC_BANNER_COMPACTO` |
| Tratamento de fotografia, grade e ilustrações | `PENDENTE_HC_IMAGENS` |
| Confirmação das famílias tipográficas | `PENDENTE_HC_TIPOGRAFIA` |
| Foco, hover, selecionado, desabilitado e finalizado | Preencher os tokens correspondentes da matriz |
| Revisão visual e de legibilidade | `PENDENTE_HC_VALIDACAO` |

Até o preenchimento, o novo tema de alto contraste tem estado **pendente**, não “implementado”.
O tema atualmente existente pode ser preservado durante a integração, mas deve continuar
identificado como legado. Não anunciar um controle novo funcional que apenas mantenha o normal.

### Como preencher e ativar no futuro

1. Registrar a paleta e os dois assets oficiais nesta seção.
2. Preencher cada placeholder com uma cor/valor ou decisão explícita de manter o normal.
3. Declarar os overrides semânticos em `:root[data-theme="high-contrast"]`.
4. Migrar todas as propriedades consumidoras, incluindo exceções de tema e literais, para tokens.
5. Integrar o acionador acessível, testar os dois sentidos e só então marcar o modo como pronto.

Modelo **comentado e não ativável**, para evitar CSS inválido enquanto faltam valores:

```css
/*
:root[data-theme="high-contrast"] {
  --color-page: <PENDENTE_HC_PAGE>;
  --color-surface: <PENDENTE_HC_SURFACE>;
  --color-text: <PENDENTE_HC_TEXT>;
  --color-hero-surface: <PENDENTE_HC_HERO_SURFACE>;
  --color-hero-text: <PENDENTE_HC_HERO_TEXT>;
  --color-action-surface: <PENDENTE_HC_ACTION_SURFACE>;
  --color-action-text: <PENDENTE_HC_ACTION_TEXT>;
  ... preencher TODOS os demais papéis da matriz antes de ativar ...
}
*/
```

Não definir `--color-text: PENDENTE`, nem depender de `var(--hc-text, ...)` para mascarar
que o modo ainda não existe. No primeiro caso, a propriedade consumidora pode ficar inválida;
no segundo, a ausência da identidade passaria despercebida.

### Mecânica de troca de cores

A troca futura altera o atributo no `html`, sem recarregar, abrir outra página ou trocar conteúdo.
Os aliases de cada tema devem ser declarados no mesmo elemento raiz. A cascata atualiza todas
as regras que consomem `var(--color-...)`; não é necessário percorrer as tags em JavaScript.

O acionador futuro será um `button type="button"` com nome acessível “Alto contraste” e
`aria-pressed` indicando o estado, com ativação por Enter/Espaço e foco preservado.
Persistência pode usar uma chave própria, por exemplo `portas-abertas-theme`, aceitando apenas
temas disponíveis. A preferência antiga `uffs-high-contrast` pertence ao exportado e não deve
ser assumida nesta implementação. Preferência por tema escuro do sistema não escolhe alto
contraste automaticamente.

Não alterar famílias, pesos, tamanhos, ordem, rolagem, filtros, grupos abertos ou posição do
carrossel ao trocar o modo. Não usar `filter: invert()` nos banners ou na página.
A proposta é troca imediata de cores, sem animação entre paletas. Transições de hover existentes
continuam independentes e devem respeitar `prefers-reduced-motion`.

## Referências históricas

Os levantamentos anteriores foram consolidados aqui; suas versões completas permanecem no
histórico Git (por exemplo, `git show 90c10bc:frontend/DESIGN.old.md` e
`git show 90c10bc:frontend/DESIGN.new.md`). Eles registram referências de 2025, não regras
concorrentes para a home atual.

Os levantamentos anteriores e assets históricos permanecem acessíveis no histórico Git, mas não
fazem parte da árvore de runtime e não são importados pela home.
O atributo histórico `data-contrast` e a chave `uffs-high-contrast` não fazem parte do contrato atual.

## Validação

Usar os comandos reproduzíveis do [README](README.md). Conferir cores computadas, faces locais,
assets desktop/móvel e proporção, ausência de overflow, foco/teclado, swipe curto e longo,
indicadores, ciclo contínuo, resize, autoplay e falha de rede. Ao receber o novo alto contraste,
validar todos os pares e assets antes de declarar o modo implementado.

## Referências para implementação

Use estas referências quando uma alteração exigir uma decisão de interação, layout ou token. Elas
orientam a implementação; não substituem os contratos específicos deste documento.

- [Material Design 3 — tipografia](https://m3.material.io/styles/typography/overview) — papéis,
  escala e hierarquia de texto.
- [Material Design 3 — botões](https://m3.material.io/components/buttons) — hierarquia e estados
  de ações.
- [Material Design 3 — estados](https://m3.material.io/foundations/interaction/states/overview) —
  foco, hover, pressionado e desabilitado.
- [Fluent 2 — tipografia](https://fluent2.microsoft.design/typography) — rampa tipográfica e
  pesos para interfaces responsivas.
- [Carbon — ações comuns](https://carbondesignsystem.com/patterns/common-actions/) — escolha e
  agrupamento de ações em componentes.
- [GOV.UK — botões](https://design-system.service.gov.uk/components/button/) — conteúdo,
  tamanho e comportamento de botões acessíveis.
- [GOV.UK — títulos](https://design-system.service.gov.uk/styles/headings/) — níveis semânticos e
  ordem de títulos.
- [W3C — propriedades personalizadas CSS](https://www.w3.org/TR/css-variables-1/) e
  [Design Tokens Community Group](https://www.designtokens.org/tr/drafts/format/) — nomes,
  escopo e interoperabilidade dos tokens.
- [MDN — propriedades personalizadas CSS](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Cascading_variables/Using_custom_properties)
  — declaração, fallback e uso de `var()`.
- [MDN — Flexbox](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Flexbox)
- [MDN — `-webkit-tap-highlight-color`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/-webkit-tap-highlight-color)
  — feedback nativo de toque em navegadores móveis e sua neutralização controlada.
  e [`overflow`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/overflow)
  — alinhamento e contenção do carrossel.

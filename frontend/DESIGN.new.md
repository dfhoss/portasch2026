# Nova identidade visual — UFFS de Portas Abertas

## Escopo e estado

Referência criada em **17/09/2026** para a reconstrução do frontend. Define a paleta recebida,
sua aplicação proposta aos componentes existentes e o contrato para receber o alto contraste.

**Modo normal:** artes e nove cores recebidas; aplicação aos componentes implementada abaixo.
**Alto contraste:** identidade ainda não recebida; todos os valores desse modo estão pendentes.
O modo normal está implementado por `fonts.css`, `tokens.css`, `main.css` e `schedule.css`.
O [DESIGN.old.md](DESIGN.old.md) permanece como registro histórico; o [DESIGN.md](DESIGN.md)
descreve as regras efetivas da home.

Seguir o modelo de [tokens do backend](../backend/DESIGN.md): separar valores primitivos de papéis
semânticos. A identidade do painel administrativo não substitui a identidade pública.

## Materiais recebidos e extração

| Material | Dimensão real | Uso |
| --- | --- | --- |
| [Banner horizontal histórico](<static/assets/images/Cópia de SITE HOME PORTAS ABERTAS UFFS 2025 (1900 x 400 px).png>) | 1900 × 400; proporção 4,75:1 | Referência histórica; não selecionado pelo hero |
| [Hero desktop](static/assets/images/hero-desktop.jpg) | 5938 × 1250; proporção 4,75:1 | Arte integral ativa acima de 600px |
| [Hero móvel](static/assets/images/hero-mobile.png) | 1080 × 437; proporção aproximada 2,47:1 | Arte integral para até 600px |
| [Palette.txt](static/assets/images/Palette.txt) | Nove cores HEX/RGB | Fonte dos valores primitivos |
| [Palette.png](static/assets/images/Palette.png) | 2000 × 1000 | Conferência visual e amostragem das faixas |

O segundo arquivo **não é vertical 9:16**. Usar suas dimensões reais no layout.
As nove faixas foram amostradas no centro e coincidem exatamente com os valores de `Palette.txt`.
A faixa preta inferior da imagem não consta da lista de nove cores; não foi incorporada como
décima cor de marca. Preto/branco presentes nas fotografias e contornos são diferentes de uma
paleta formal da interface.

Os nomes exportados como `--#ed53c5` não devem ser copiados como identificadores CSS:
usar nomes legíveis e válidos, como `--palette-magenta`.

### Paleta primitiva recebida

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

A extração é da paleta fornecida, não uma promessa de que cada pixel dos banners tem esses valores.
Fotografia, transparência e suavização produzem outras cores. Preservar as diferenças entre
`#393aed`, `#393cb3` e `#352aff`; não tratá-las como grafias da mesma cor.

## Linguagem visual

A composição recebida usa fundo verde-limão, grade clara, marca azul-violeta, círculo rosa,
faixas retangulares, contornos em degraus e ilustrações pixeladas. A fotografia do campus e das
pessoas se mistura à base de vegetação pixelada. A marca distingue PORTAS leve de ABERTAS pesado;
UFFS DE tem linguagem pixelada.

Na interface, reservar essa expressão mais intensa para banner, destaques e ações.
Agenda e regulamento precisam de leitura contínua: superfícies claras, hierarquia consistente,
texto escuro e espaço suficiente. Rosa, verde vivo e violeta elétrico permanecem disponíveis para
ilustração e detalhes; não atribuir automaticamente significado de erro, sucesso ou categoria a eles.

**Decisões propostas para UI, não especificações extraídas das artes:** fundo geral verde
acinzentado, cartões brancos, neutros escuros de texto, bordas índigo, estados interativos,
sombras e opacidade da grade. Esses papéis tornam o material utilizável no site; os PNGs não
definem estilos para cada controle.

## Estado da implementação examinada

- `index.html` já declara `<html lang="pt-BR" data-theme="standard">`.
- `static/css/fonts.css` e `static/css/tokens.css` são carregados antes dos componentes; `main.css`
  e `schedule.css` consomem esses tokens sem cores de marca literais.
- `static/css/schedule.css` mantém os consumidores da agenda e os seletores
  `data-theme="high-contrast"` e `data-theme="dark"`.
- Há exceções por tema em seleção de visão, summaries, contagens, cursos, horários, links e
  regulamento; algumas usam o literal `#14152b`. Alterar só `:root` não elimina essas exceções.
- A home contém Rolando agora, programação completa com seleção de visão e grupos expansíveis,
  regulamento e uma seção de mapa ainda incompleta.
- Os scripts carregados são `carousel.js` e `schedule.js`. Não foi encontrado nesses arquivos
  um controlador de troca de tema. A assinatura CONTRASTE do banner é uma `div`, não um botão.

Manter **`data-theme="standard|high-contrast"`** como contrato da reconstrução.
Não importar o atributo `data-contrast` do exportado antigo. O alias `dark` hoje existente
é legado: não significa que já recebemos uma identidade nova de alto contraste.

## Tokens CSS do normal

Bloco efetivo da folha central de tokens, carregada antes de `main.css` e
`schedule.css`; declarações antigas duplicadas que sobrescreviam esses valores foram removidas.
As duas folhas consomem essa única fonte de tokens.

Os nove `--palette-*` são recebidos. Branco, neutros de leitura e valores com alpha são
complementos funcionais propostos, identificados nos papéis abaixo.

```css
:root {
  --palette-magenta: #ed53c5;
  --palette-violet: #393aed;
  --palette-green-bright: #14d204;
  --palette-pink: #fda2e3;
  --palette-sage: #d2decf;
  --palette-indigo: #393cb3;
  --palette-green: #368a2e;
  --palette-lime: #d8f93b;
  --palette-violet-electric: #352aff;

  --color-page: var(--palette-sage);
  --color-surface: #ffffff;
  --color-brand: var(--palette-violet);
  --color-brand-soft: var(--palette-indigo);
  --color-accent: var(--palette-lime);
  --color-accent-line: var(--palette-lime);
  --color-live: var(--palette-magenta);
  --color-text: #171725;
  --color-text-muted: #42434d;
  --color-tag-surface: var(--palette-sage);
  --color-tag-text: var(--palette-indigo);
  --color-border: var(--palette-indigo);
  --color-border-hover: var(--palette-violet);
  --color-focus: var(--palette-violet);
  --color-focus-ring: var(--palette-lime);
  --color-card-shadow: rgb(57 60 179 / 8%);
  --color-card-shadow-hover: rgb(57 60 179 / 14%);
  --color-finalized-surface: var(--palette-sage);
  --color-finalized-text: #42434d;
  --color-finalized-border: var(--palette-indigo);
  --color-finalized-badge: var(--palette-indigo);
  --color-finalized-badge-text: #ffffff;
  --color-hero-surface: var(--palette-lime);
  --color-hero-text: var(--palette-violet);
  --color-hero-grid: rgb(255 255 255 / 55%);
  --color-badge-surface: var(--palette-violet);
  --color-badge-text: var(--palette-lime);
  --color-action-surface: var(--palette-violet);
  --color-action-text: var(--palette-lime);
  --color-action-hover: var(--palette-indigo);
  --color-selected-surface: var(--palette-violet);
  --color-selected-text: var(--palette-lime);
  --color-link: var(--palette-indigo);
  --color-link-hover: var(--palette-violet);
  --color-status-live-surface: var(--palette-magenta);
  --color-status-live-text: #171725;
  --color-status-soon-surface: var(--palette-lime);
  --color-status-soon-text: var(--palette-indigo);
  --color-disabled-surface: var(--palette-sage);
  --color-disabled-text: #42434d;
  --color-field-surface: #ffffff;
  --color-field-text: #171725;
  --color-placeholder: #42434d;
  --color-selection-surface: var(--palette-indigo);
  --color-selection-text: #ffffff;
}
```

Não usar `--color-brand` como um token universal para texto sobre qualquer fundo. Usar pares
explícitos: ação/texto da ação, seleção/texto selecionado, status/texto do status.
A mesma cor primitiva pode servir a vários papéis no normal e divergir no alto contraste.

## Matriz de troca e placeholders de alto contraste

Cada linha é uma decisão a preencher quando a identidade chegar. Os identificadores
`PENDENTE_HC_*` são **marcadores de documentação, não valores CSS válidos**.
Nenhuma célula pendente autoriza reaproveitar automaticamente o tema escuro atual ou o antigo.

| Token semântico | Normal proposto | Alto contraste a receber | Consumidor / finalidade |
| --- | --- | --- | --- |
| `--color-page` | `var(--palette-sage)` | `PENDENTE_HC_PAGE` | body; fundo geral |
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

## Mapa de componentes e tags

| Elementos atuais | Consumo previsto / migração |
| --- | --- |
| `body`, `main`, `section`, `article`, wrappers | `page`, `surface`, `text`; contêiner transparente herda cor/fonte |
| `.banner`, `.title`, `.badge` | Pares `hero-*` e `badge-*`; substituir o fundo violeta/padrão de círculos pela composição nova quando integrar |
| `h1`–`h6`, `p`, `span`, `strong`, `time` | Cor contextual; `strong` altera peso, não cria outra paleta; remover cores inline/literais conflitantes |
| `.activity-card`, títulos, local e descrição | `surface`, `text`, `text-muted`, `brand`, bordas e sombras |
| `.status-badge.live`, `.status-badge.soon`, `.live-dot` | Pares `status-live-*`, `status-soon-*`; ponto usa `live`; manter rótulos |
| `.carousel-btn`, `.dot.active` | Pares `action-*`, `selected-*`, `disabled-*`; foco visível |
| Seletor `.schedule-view-selector__option` | Estado `aria-checked="true"` usa `selected-surface/text`; migrar literal escuro |
| `details`, `summary`, `.schedule-view-group*` | Superfície, borda, foco, par selecionado para indicador; `::after` também participa |
| Cursos, atividades, sessões, contagens e tags | `brand`, `text`, `text-muted`, `tag-surface/text`; retirar exceções que só funcionam com o tema antigo |
| `.schedule-item--finalized` | Todos os `finalized-*`, incluindo texto do badge; preservar indicação textual de finalização |
| `.rule-card*`, `.rule-btn`, listas e marcadores | Superfície, texto e pares de ação; `li::before` usa destaque e não comunica estado sozinho |
| `a` e estados `:visited`, `:hover`, `:focus-visible` | `link/link-hover` em fundo claro; sobre botão/célula, herdar seu par; preservar sublinhado |
| `button`, `input`, `select`, `textarea` (quando usados) | Herdar fonte explicitamente, usar pares de ação/campo e foco; placeholder usa token próprio |
| `table`, `th`, `td` (se adicionados) | Definir superfície/texto por papel, nunca copiar cores por índice de célula do Canva |
| `svg`, `path`, `polyline`, `circle` | Ícones monocromáticos usam `currentColor`; preservar `fill="none"` quando exigido |
| `::before`, `::after`, bordas, sombras, `::selection` | Participam da tokenização; seleção tem par próprio |
| `img`, `picture`, `canvas`, `iframe` | Conteúdo interno não é recolorido pelos tokens; necessita asset/estratégia específica |
| `br`, metadados, scripts e estilos | Não têm paleta visual própria |

`color` e fonte são herdados; fundos e bordas não. Um filho com cor fixa bloqueia a aparência
pretendida pelo pai. Para elementos novos, declarar superfícies junto de seus textos; não usar
um seletor universal que force fundo ou cor em todas as tags.

## Banners, responsividade e conteúdo acessível

Usar o PNG horizontal histórico apenas como referência de composição. O hero ativo usa as artes
completas `hero-desktop.jpg` e `hero-mobile.png`; não sobrepor o título antigo, óculos ou badge HTML sobre
o mesmo conteúdo já embutido na imagem. Não cortar campus, marca, data e horário com `cover`.

A implementação de imagem integral usa `display: block; width: 100%; height: auto`, reservando
a proporção via atributos `width`/`height`. Não impor ao banner 1900 × 400 a altura
`clamp(280px, 36vw, 480px)` da composição antiga. O arquivo compacto é a arte móvel confirmada
e é selecionado pelo `picture` até 600px.

As artes incluem “27 de outubro”, “08h30 às 21h” e “Campus Chapecó”. Registrar isso como conteúdo
da imagem recebida, sem inferir o ano ou substituir os dados do backend a partir do nome do arquivo.
Se essas informações forem relevantes à navegação, devem ter equivalente textual atualizado.
Usar alt informativo quando a arte for a única fonte; usar alt vazio quando o texto adjacente
já comunicar integralmente as mesmas informações. Manter um h1 semântico e evitar anúncio duplicado.

Quando vier o alto contraste, trocar o asset por sua versão oficial de acordo com o mesmo tema.
CSS muda o entorno, mas não muda textos e fundos dentro do PNG. Reservar ambos os caminhos
pendentes acima; não inventar nomes de arquivos existentes.

## Tipografia

As novas entregas são rasterizadas: não contêm metadados suficientes para certificar famílias.
Visualmente mantêm linguagem monoespaçada/pixelada, mas essa observação não confirma o nome de
cada fonte. As famílias reais extraídas anteriormente estão disponíveis em
[fonts.css](static/design-old/fonts.css) e no [manifesto](static/design-old/fonts-manifest.json).

Proposta de continuidade até receber especificação tipográfica nova:

| Papel | Família real proposta | Peso |
| --- | --- | --- |
| PORTAS / ABERTAS e títulos curtos | Disket Mono | 400 / 700 |
| UFFS DE / detalhe pixelado curto | Retropix | 400 |
| Corpo, descrição e agenda | Open Sans | 400; 700 para ênfase |
| Informações auxiliares | Garet | 400 / 700 |
| Controle de contraste | Open Sans | 700 |

A família da data e do horário embutidos no PNG permanece **a confirmar**; não inferir Antonio
apenas pela aparência estreita. League Spartan, Antonio e Fira Sans continuam disponíveis no
registro antigo, sem obrigatoriedade de uso na nova interface.

Tokens tipográficos propostos, preservando os nomes consumidos pela agenda:

```css
:root {
  --font-heading: "Disket Mono", "Courier New", monospace;
  --font-mono: "Disket Mono", "Courier New", monospace;
  --font-body: "Open Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-pixel: "Retropix", monospace;
  --font-info: "Garet", Arial, sans-serif;
  --font-size-sm: 0.875rem;
  --font-size-body: 1rem;
  --font-size-title: clamp(1.5rem, 3vw, 2.25rem);
  --font-weight-regular: 400;
  --font-weight-bold: 700;
  --line-height-body: 1.5;
  --line-height-heading: 1.2;
}
```

As faces locais são carregadas por `fonts.css`; os pesos de Disket Mono disponíveis são 400/700,
sem peso 900 sintético.
Rótulos de leitura longa permanecem em caixa de frase. A marca pode manter caixa alta.
Fonte deve ter fallback, e o tema não muda a hierarquia tipográfica.

## Layout e interação preservados

A identidade nova não exige alterar o comportamento já implementado. Manter raios de cartões
16px, raio menor 8px, badge 4px, pílulas e bordas de 2px como continuidade funcional proposta.
Os contornos em degraus da arte ficam no banner; não obrigam todos os cartões a assumir pixel art.

No carrossel, preservar 3 cartões acima de 900px, 2 entre 601px e 900px e 1 até 600px, gap
compartilhado de 20px, autoplay de 5s, debounce de resize de 150ms, navegação por teclado e
swipe acima de 50px. A escolha de banner compacto não muda esses breakpoints.

Preservar seleção de visão, expansão de grupos e leitura de agenda/eixos/locais diretamente dos
JSONs do backend. Troca de tema não deve recriar dados nem recolher grupos.

## Checklist de integração e aceite

- Centralizar tokens, eliminar cores fixas e overrides antigos conflitantes das duas folhas.
- Conferir estados normal, hover, foco, selecionado, desabilitado e finalizado.
- Medir contraste dos pares efetivamente usados, inclusive textos pequenos; magenta, rosa e
  verde vivo não devem ser escolhidos como texto em branco por suposição de legibilidade.
- Confirmar fontes e pesos disponíveis; validar leitura sem carregamento de fontes.
- Verificar desktop/tablet/celular, zoom, ausência de overflow, proporções e leitura dos banners.
- Testar Tab, Enter/Espaço no acionador futuro, setas e swipe no carrossel.
- Após receber alto contraste, preencher a matriz inteira, testar standard → high-contrast →
  standard e verificar imagens, pseudo-elementos, links visitados, foco e estados restaurados.
- DESIGN.md e README.md registram o carregamento efetivo da identidade normal e do hero.

Validação deste documento: leitura dos estilos e scripts atuais, inspeção visual dos banners,
suíte de identidade e conferência dos nove HEX por amostragem do Palette.png. Os placeholders
de alto contraste permanecem intencionais e solicitados; o modo normal está implementado.

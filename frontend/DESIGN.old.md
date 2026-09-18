# Design histórico — Portas Abertas 2025

## Objetivo e fontes de verdade

Documentar os modos normal/claro e alto contraste/escuro do site antigo para orientar a
reconstrução do frontend. A organização segue o [DESIGN do backend](../backend/DESIGN.md):
primitivos, tokens semânticos, tipografia, regras de uso e validação. A paleta verde e a fonte
de sistema do painel administrativo **não** são a identidade do site público antigo.

Referências inspecionadas em **16/09/2026**, usando o MCP do Playwright:

- [Publicação normal](https://linksdesites.my.canva.site/portas-abertas-2025-uffs).
- [Publicação de alto contraste](https://linksdesites.my.canva.site/c-pia-de-portas-abertas-2025-uffs).
- Exportação local: `C:/Users/Administrador/Desktop/projetos/portas-abertas-rewrite`, sobretudo
  `index.html`, `assets/js/color-mode-toggle.js`, `assets/js/high-contrast-palette.js`,
  `assets/js/local-mode-links.js` e `assets/site/fonts/`.

As publicações são a referência de aparência; a cópia fornece os arquivos e explica a
implementação local. Divergências de conteúdo e posicionamento não são regras de tema.
Este documento registra o histórico e não substitui o [DESIGN atual](DESIGN.md).
Nenhuma folha deste levantamento está importada pela home atual.

### O que “escuro” significa aqui

O modo denominado alto contraste **não escurece a página inteira**. O fundo principal continua
`#fffff6`; a feira usa `#ffffff`. Banner, células e algumas faixas ficam azuis escuras;
textos sobre essas superfícies tornam-se claros. Mapas e redes sociais conservam exceções.
Não equivale a `prefers-color-scheme: dark`, a `forced-colors`, nem a um filtro `invert()`.
O nome do modo não constitui, por si só, uma certificação de acessibilidade.

## Arquivos de referência

| Arquivo | Finalidade |
| --- | --- |
| [tokens.css](static/design-old/tokens.css) | Paleta completa, famílias, medidas de autoria e papéis para ambos os modos |
| [fonts.css](static/design-old/fonts.css) | 16 declarações `@font-face`, de sete famílias locais |
| [fonts-manifest.json](static/design-old/fonts-manifest.json) | Família, peso, estilo, origem, tamanho e SHA-256 de cada WOFF |
| [fonts/](static/design-old/fonts/) | Cópias dos arquivos originais, nomeadas por família, peso e estilo |
| [evidence.json](static/design-old/evidence.json) | Amostras de estilos computados, células serializadas, tags e resultados dos cliques |

Os nomes `--old-*` foram criados para tornar a referência legível e isolada.
As declarações CSS usam os nomes reais das famílias. O Canva não usava estes tokens: usava estilos inline, classes geradas, fontes com IDs
e um documento serializado. Os valores históricos vêm dessas fontes, não de estimativa visual.

## Paleta primitiva

| Token | Valor | Uso histórico |
| --- | --- | --- |
| `--old-violet` | `#393ce4` | Banner normal |
| `--old-navy` | `#25265a` | Banner, células e títulos no alto contraste |
| `--old-blue` | `#004aad` | Badge e grupos de cursos no alto contraste |
| `--old-petrol` | `#015a83` | Texto normal e cabeçalho da agenda |
| `--old-blue-text` | `#144e99` | Informações em Garet, atividades e intervalos |
| `--old-lime` | `#d7f932` | Células de atividades, UFFS DE e controle normal |
| `--old-yellow` | `#e3ff00` | PORTAS ABERTAS, gincana e separadores inferiores |
| `--old-magenta` | `#ed54ce` | Badge normal, chamadas e separadores |
| `--old-pink` | `#ffa5ed` | Faixas de grupos da agenda normal |
| `--old-paper` | `#fffff6` | Superfície clara predominante |
| `--old-white` | `#ffffff` | Feira; texto serializado em células da gincana de alto contraste |
| `--old-light-text` | `#f1f2f2` | Texto principal sobre áreas escuras |
| `--old-black` | `#000000` | Exceção do título “Mapa do campus” no alto contraste |

`#d7f932` e `#e3ff00` são diferentes. Também não substituir `#fffff6` pelo `#f8f8f0`
do frontend atual. Cores contidas em imagens/padrões do Canva não foram convertidas em tokens:
um fundo computado não descreve sozinho o pixel resultante de uma imagem sobreposta.

## Mapa de troca por função

Valores à direita são os da publicação de alto contraste, não uma substituição global por hex.
Os nomes abaixo omitem apenas o prefixo `--old-` para facilitar a leitura.

| Token semântico / contexto | Normal | Alto contraste |
| --- | --- | --- |
| `page-bg` — conteúdo geral | `#fffff6` | `#fffff6` |
| `fair-bg` — feira de ciências | `#ffffff` | `#ffffff` |
| `hero-bg` | `#393ce4` | `#25265a` |
| `hero-text` — PORTAS e ABERTAS | `#e3ff00` | `#f1f2f2` |
| `badge-bg` — faixa UFFS DE | `#ed54ce` | `#004aad` |
| `badge-text` — UFFS DE | `#d7f932` | `#f1f2f2` |
| `toggle-text` — texto/ícone do controle | `#d7f932` | `#f1f2f2` |
| `top-divider` — separação superior da programação | `#d7f932` | `#ed54ce` |
| `lower-divider` — separadores inferiores da gincana/mapas | `#e3ff00` | `#e3ff00` |
| `section-text` — programação completa/feira | `#015a83` | `#25265a` |
| `info-text` — intervalos e atividades culturais | `#144e99` | `#25265a` |
| `table-head-bg` — cabeçalho de colunas | `#015a83` | `#25265a` |
| `table-head-text` | `#fffff6` | `#f1f2f2` |
| `table-row-bg` — atividade, horário, descrição | `#d7f932` | `#25265a` |
| `table-row-text` | `#015a83` | `#f1f2f2` |
| `table-group-bg` — faixa de curso, exemplo Ciência da Computação | `#ffa5ed` | `#004aad` |
| `table-group-text` | `#015a83` | `#f1f2f2` |
| `table-admin-bg` — exceção observada: Administração | `#ffa5ed` | `#25265a` |
| `table-gap` — espaço entre células | `#fffff6` | `#fffff6` |
| `game-badge-bg` — faixa GINCANA | `#e3ff00` | `#25265a` |
| `game-badge-text` | `#015a83` | `#f1f2f2` |
| `game-cell-bg` — participantes | `#e3ff00` | `#25265a` |
| `game-cell-text` | `#015a83` | `#ffffff` (*) |
| `game-callout-text` — equipes/regulamento | `#ed54ce` | `#25265a` |
| `map-campus-text` | `#015a83` | `#000000` |
| `map-blocks-text` | `#015a83` | `#015a83` |
| `social-text` — título, perfis e site | `#015a83` | `#015a83` |
| `fair-location-text` — localização da feira | Sem texto equivalente renderizado | `#015a83` |

(*) A tabela de participantes da publicação de alto contraste está vazia. `#ffffff` é o valor
dos estilos serializados de suas células, não uma observação de nomes visíveis. A primeira célula
vazia ainda declara `#015a83`; não usar esse resíduo para desenhar texto novo sobre azul-escuro.

A seção “rolando agora” está presente no normal, mas não foi renderizada na publicação de alto
contraste. No normal, o título usa `#015a83`, informações usam `#144e99` e CHECK-IN usa `#f1f2f2`.
Não existe um par visual publicado para certificar o tema dessa seção. Para reconstruí-la nos dois
modos, aplicar os papéis de superfície/texto correspondentes é uma decisão de implementação.

## Como o clique funciona

### Nas publicações do Canva

1. No normal, o link visível é **CONTRASTE**.
2. Ele abre uma nova aba para
   `https://mundomakechp.my.canva.site/c-pia-de-portas-abertas-2025-uffs`.
3. No alto contraste, **SEM CONTRASTE** abre outra aba para
   `https://mundomakechp.my.canva.site/portas-abertas-2025-uffs`.
4. Ambos os destinos antigos retornaram uma página intitulada **Não encontrado** na inspeção.
   As duas URLs `linksdesites` fornecidas para este levantamento funcionaram diretamente.

Portanto, o clique publicado é uma navegação entre documentos, não uma animação de CSS nem
uma troca de classe na mesma página. Além das cores, os documentos divergem em tamanho do título,
seções, linhas da agenda e conteúdo da gincana. Essas diferenças não devem ocorrer apenas porque
o usuário mudou o contraste na reconstrução.

### Na cópia local

O ciclo foi conferido por clique nos dois sentidos em `http://127.0.0.1:4174/`:

1. `color-mode-toggle.js` lê `localStorage['uffs-high-contrast'] === 'true'` e publica
   `data-contrast="high"` ou `data-contrast="standard"` no `html`.
2. Ajusta o rótulo, `role="switch"`, `aria-checked` e o nome acessível
   “Ativar alto contraste” / “Desativar alto contraste”. O ícone duplicado sai da ordem de Tab.
3. O clique é interceptado; inverte a preferência, salva a rolagem em
   `sessionStorage['uffs-contrast-scroll-y']` e chama `window.location.reload()`.
4. Antes de o runtime do Canva renderizar, `high-contrast-palette.js` altera o `window.bootstrap`
   usando **596 operações por ID e caminho**. Só executa quando a preferência é `true`.
5. Um fallback percorre as strings restantes: `#e3ff00 → #f1f2f2` e
   `#d7f932 → #ed54ce`. Ele não conhece a função de cada cor.
6. `local-mode-links.js` redireciona os links do Canva para a raiz local. Um `MutationObserver`
   reaplica os rótulos aos nós criados pelo runtime. Após o carregamento, tenta restaurar a rolagem.

O atributo `data-contrast` **não recolore sozinho** o exportado: os valores estão nos dados e
nos estilos inline gerados. A atualização ocorre no recarregamento; não há um crossfade de tema
definido por esse mecanismo. O script de clique não contém tratamento de tecla Espaço para o
link com `role="switch"`; a semântica de switch não deve ser copiada sem seu contrato de teclado.

### Por que algumas cores da cópia divergem

Todas as 596 operações encontram caminhos existentes na exportação examinada. Isso não garante
que encontrem o **mesmo conteúdo**: as posições de linhas mudaram entre as publicações.

| Célula do mesmo ID `LBkJr0cb2mLJKN4M` | Normal/exportação | Alto contraste publicado |
| --- | --- | --- |
| `A10` | Máquinas Agrícolas | CIÊNCIA DA COMPUTAÇÃO |
| `A11` | CIÊNCIA DA COMPUTAÇÃO | Oficina de Circuitos |
| `A12` | Oficina de Circuitos | Oficina de Programação |

Assim, uma operação que pinta `A10` de `#004aad` atinge uma atividade na cópia, embora no documento
de origem fosse uma faixa de curso. `A11` recebe o azul de atividade embora contenha o curso.
Outra lacuna: o fundo do cabeçalho normal `#015a83` não aparece entre as substituições de fundo
para `#25265a`, apesar de essa ser a cor publicada no alto contraste.

O fallback também troca amarelos que o alto contraste publicado preserva em separadores inferiores.
Há inclusive três destinos diferentes para o mesmo verde `#d7f932` nas operações específicas:
azul-escuro, azul e texto claro. Logo, procurar/substituir cores globalmente perde informação.

Na reconstrução, escolher o token pelo **papel do elemento** e pelo dado que ele representa.
Não copiar IDs/índices do Canva, posições `A10`, seletores ofuscados ou a lista de 596 operações.

## Tokens CSS e contrato de consumo

A declaração completa e reutilizável está em [tokens.css](static/design-old/tokens.css).
Exemplo de carregamento futuro, relativo a uma página na raiz de `frontend`:

```html
<html lang="pt-BR" data-legacy-design data-contrast="standard">
  <head>
    <link rel="stylesheet" href="static/design-old/fonts.css">
    <link rel="stylesheet" href="static/design-old/tokens.css">
  </head>
</html>
```

O `data-legacy-design` isola a referência do frontend atual. `standard` é normal/claro;
`high` é alto contraste histórico. Na ausência de `data-contrast`, prevalecem os tokens normais.
Não adicionar leitura automática do tema do sistema ao registro histórico.

As regras de tema declaram os aliases semânticos **no mesmo `:root`** que as primitivas.
Os componentes consomem os aliases; não precisam saber qual modo está ativo. Por exemplo:

```css
html[data-legacy-design] body {
  background-color: var(--old-page-bg);
  color: var(--old-body-text);
  font-family: var(--old-font-body);
}

.legacy-hero {
  background-color: var(--old-hero-bg);
  color: var(--old-hero-text);
  font-family: var(--old-font-display);
}
.legacy-hero-title { color: inherit; }
.legacy-hero-title strong { font-weight: var(--old-weight-bold); }
.legacy-badge {
  background-color: var(--old-badge-bg);
  color: var(--old-badge-text);
  font-family: var(--old-font-pixel);
}
.legacy-contrast-toggle {
  color: var(--old-toggle-text);
  background: transparent;
  font-family: var(--old-font-toggle);
}
.legacy-contrast-toggle:focus-visible {
  outline: 3px solid var(--old-focus-on-dark);
  outline-offset: 4px;
}
.legacy-agenda { font-family: var(--old-font-body); }
.legacy-agenda :is(th, td) {
  background-color: var(--old-table-row-bg);
  color: var(--old-table-row-text);
}
.legacy-agenda thead th {
  background-color: var(--old-table-head-bg);
  color: var(--old-table-head-text);
}
.legacy-agenda .course-group > :is(th, td) {
  background-color: var(--old-table-group-bg);
  color: var(--old-table-group-text);
}
.legacy-agenda .course-group--administracao > :is(th, td) {
  background-color: var(--old-table-admin-bg);
}
.legacy-agenda :is(p, span, a) { color: inherit; }
.legacy-agenda a { text-decoration: underline; }
```

O exemplo só demonstra consumo; não é uma nova home. A classe de Administração registra uma
exceção visual publicada, não a posição da linha. Para preservar a aparência histórica,
os papéis de mapa e redes precisam ser explícitos, pois não herdam a troca do texto geral.

### Herança, propriedades e transição temporal

`color` e `font-family` normalmente são herdados; `background-color` e bordas não. Um `span`
com `style="color: #015a83"` continua azul mesmo que o pai receba texto claro. Remover esse valor
literal ou substituí-lo por `inherit`/token é parte da reconstrução. O mesmo vale para
`-webkit-text-fill-color`, `text-shadow`, pseudo-elementos e decorações explícitas.

A referência usa `--old-mode-duration: 0ms`: representa troca direta, sem inventar duração para
as publicações. Se o novo produto optar por transição suave, essa será uma decisão adicional;
animar as propriedades consumidoras (`color`, `background-color`, `border-color`, `fill`,
`stroke`, `outline-color`) e respeitar `prefers-reduced-motion`. Não usar `transition: all`,
nem interpolar tamanhos/fontes como parte da mudança de contraste. A preferência reduzida deve
voltar a `0ms` e não introduzir intervalo com texto ilegível entre duas superfícies.

`color-scheme: light` permanece na referência porque as superfícies gerais históricas são claras.
Isso só informa a aparência nativa ao navegador; não implementa a paleta da aplicação.

## Cobertura das tags HTML

A cor é definida pelo contexto e pelo papel, não por uma regra universal “todo `div` escurece”.
O inventário de tags realmente encontrado está em `evidence.json`. O Canva usa muitos `p`/`span`
para títulos; a reconstrução deve empregar headings semânticos. As linhas de extensão abaixo
cobrem elementos que podem surgir no HTML novo, sem atribuir ao Canva estilos que não existiam.

| Tags / elementos | Cor, fundo e fonte na troca |
| --- | --- |
| `html`, `body` | Recebem tokens e estabelecem superfície geral, texto e Open Sans. O fundo permanece papel. |
| `main`, `section`, `div` | Herdam texto/fonte; fundo transparente até um papel explícito definir superfície. O banner usa o par `hero-*`; a feira usa `fair-bg`. |
| `header`, `footer`, `nav`, `article`, `aside` (extensão) | Mesma regra de contêiner; `footer` de redes usa `social-text`, não o texto geral do modo. |
| `h1`–`h6` (semântica reconstruída) | Disket Mono para títulos editoriais; `hero-text`, `section-text`, `game-callout-text` ou token de mapa conforme o papel. Não trocar de família ao mudar o modo. |
| `p`, `span` | Herdam a cor do bloco. Corpo de agenda usa Open Sans; informação usa Garet. Limpar cores inline antigas. |
| `a`, `a:visited`, `a:hover`, `a:active` | Herdar a cor do contexto ou consumir o token específico do controle/redes; manter sublinhado ou outro sinal de link. Não permitir roxo nativo em célula escura. |
| `strong`, `b`, `em`, `i`, `small`, `time`, `abbr`, `sub`, `sup` (extensão) | Herdar cor e família; só peso, estilo ou tamanho muda conforme a semântica. Peso real exige a face correspondente. |
| `ul`, `ol`, `li`, `dl`, `dt`, `dd` (extensão) | Herdar texto/fonte do conteúdo; `::marker` acompanha `currentColor`. |
| `table`, `thead`, `tbody`, `tfoot`, `tr`, `th`, `td`, `caption` | Aplicar pares de cabeçalho, grupo ou atividade às células. `p`/`span` internos herdam. `caption` fica sobre a superfície externa. A agenda deve usar `th` com escopo, mesmo que a exportação use `td`. |
| `button` | A publicação usa links para contraste; botões da infraestrutura Canva não são tokens da marca. Em controle novo, declarar `font: inherit`, par `control-*` e foco contextual. |
| `form`, `label`, `fieldset`, `legend`, `input`, `textarea`, `select`, `option`, `optgroup`, `output` (extensão) | Texto/fonte herdados explicitamente; entradas usam `control-bg`, `control-text`, `control-border`. Placeholder não substitui label; popup nativo pode depender do sistema. |
| `details`, `summary`, `dialog` (extensão) | Usar superfície/texto definidos juntos, fonte herdada e foco; `::backdrop` precisa de regra própria se existir. |
| `hr`, bordas, `::before`, `::after`, `::selection` | Aplicar tokens próprios. Separadores inferiores preservam amarelo; não confundir com a linha magenta superior. Pseudo-elementos com literal precisam migrar também. Seleção nova deve ter par legível explícito. |
| `code`, `pre`, `kbd`, `samp`, `mark`, `blockquote` (extensão) | Preservar função semântica; definir pares de texto/fundo próprios se utilizados. Não há estilo publicado desses componentes para extrair. |
| `img`, `picture`, `source`, `video`, `audio`, `canvas`, `iframe`, `object`, `embed` | Cores internas não mudam pela herança de CSS. Não aplicar filtro global; imagens e integrações ficam fora deste levantamento. |
| `br`, `wbr` | Não possuem paleta; apenas quebra de texto. |
| `head`, `title`, `meta`, `link`, `style`, `script`, `template`, `noscript` | Metadados/recursos não têm cores visíveis próprias; conteúdo visível de `noscript` herda as regras comuns. |

Para SVG inline, `svg`, `g`, `path`, `rect` e demais formas usam `fill: currentColor` ou
`stroke: currentColor` **somente quando o ícone for monocromático**. Não preencher globalmente
paths desenhados com `fill="none"`. `defs`/`clipPath` não são superfícies; `stop` de gradiente
usa `stop-color`, que exige token próprio. SVG externo carregado por `img` não herda `currentColor`.

Para elementos não previstos, herdar texto/fonte do contêiner e definir explicitamente qualquer
superfície que desenhem. Essa regra evita tentar enumerar uma cor fixa para cada tag possível.

Os tokens `control-*` e `focus-*` são uma extensão de reconstrução, diferenciada no CSS; não são
uma extração de formulários do Canva. Hover pode reforçar sublinhado/borda sem inventar uma segunda
paleta. Estados ativo, expandido e desabilitado precisam de semântica e rótulos além da cor.

## Fontes: arquivos e aplicação

Os nomes foram identificados no catálogo de fontes do `bootstrap` local e conferidos com as
declarações `@font-face` das publicações. Não foram deduzidos pela aparência. Os identificadores internos do Canva foram traduzidos para os nomes reais das famílias.
Os arquivos locais usam nomes como `disket-mono-700-normal.woff`; o manifesto preserva o caminho
original e o SHA-256 para rastreabilidade.

| Família | Papel observado | Faces copiadas |
| --- | --- | --- |
| Retropix | UFFS DE, letras pixeladas | 400 normal |
| Disket Mono | PORTAS, ABERTAS, títulos de programação, mapas, redes e chamadas da gincana | 400 e 700 normais |
| League Spartan | CONTRASTE / SEM CONTRASTE; CHECK-IN | 400 normal |
| Open Sans | Agenda e participantes da gincana | 300, 400, 700 e 800, normais e itálicos |
| Garet | Atividades, intervalos, perfis das redes | 400 e 700 normais |
| Antonio | GINCANA | 400 normal |
| Fira Sans | Localização da feira no alto contraste | 400 normal |

Arimo também consta do catálogo exportado, mas não apareceu no texto editorial
amostrado após rolar as seções. Não foi copiada. Canva Sans, fontes de fallback da plataforma e
`calibrate` pertencem à infraestrutura do exportador, não à identidade editorial.

### Escala observada e pesos

| Papel | Tamanho CSS de autoria observado | Entrelinha / particularidade |
| --- | --- | --- |
| UFFS DE | `57.8849px` | `69px`, tracking `0.15em`, Retropix 400 |
| PORTAS / ABERTAS normal | `100.445px` | `92px`; PORTAS 400, ABERTAS 700 no `span` |
| PORTAS / ABERTAS alto contraste | `141.621px` | `130px`; diferença entre documentos, não efeito obrigatório do tema |
| Controle de contraste | `37.4186px` | `41px`, League Spartan 400 |
| Título de seção | `46.6668px` | `53px` ou `64px`, geralmente Disket Mono 700 no `span` |
| Informação / intervalos | `26.6667px` | `37px`, Garet; mistura 400/700 |
| Atividade em destaque no normal | `31.9999px` | `44px`, Garet |
| Perfil de rede social | `41.1466px` | `46px`, Garet |
| Cabeçalho de agenda | `14.7098px` a `16.2589px` | `20px` a `22px`, Open Sans 700 |
| Corpo de agenda | `12px` a `13.5491px` | `16px` a `18px`, Open Sans; peso depende do trecho |
| Participantes normal | `13.3335px` | `18px`, Open Sans |
| GINCANA | `66.6667px` | `80px`, Antonio 400, tracking `0.15em` |

O `p` pode declarar 400 e conter um `span` de peso 700. Medir só o pai perde a hierarquia.
O Canva aplica escalas e transformações aos contêineres: esses valores CSS não equivalem sempre
à altura visual em pixels da captura e não devem virar tamanhos fixos no celular.
Não perpetuar texto a 12px para encaixar a nova agenda; definir uma escala responsiva legível
na implementação futura, preservando os papéis e as famílias.

As fontes **não trocam** quando se ativa contraste. Mudam texto, superfícies e detalhes de cor;
a mudança de tamanho do hero entre publicações é uma divergência de autoria já registrada.

### Uso das faces locais

```css
/* Exemplo real de fonts.css; a URL é relativa à folha, não ao HTML. */
@font-face {
  font-family: "Disket Mono";
  src: url("./fonts/disket-mono-400-normal.woff") format("woff");
  font-style: normal;
  font-weight: 400;
  font-display: swap;
}
```

Cada peso/estilo real tem sua declaração. Não declarar o mesmo arquivo estático como uma fonte
variável `100 900` só porque o exportador gerava aliases para vários pesos. Fira Sans possui
somente a face 400 nesse catálogo, embora o trecho de localização solicite 700: registrar essa
limitação em vez de chamar o arquivo de bold. Retropix, Antonio e League Spartan também têm
somente uma face fornecida. O manifesto permite distinguir arquivo disponível de peso solicitado.

O fallback de cada token mantém o texto disponível sem download. `font-display: swap` é uma
decisão de carregamento da referência reutilizável; não altera a identidade quando a fonte local
está disponível. Não são necessários Google Fonts, CDN, JavaScript ou downloads adicionais.

## Acessibilidade e limites da reprodução

Preservar `lang="pt-BR"`, landmarks, ordem de headings, labels, foco visível e acesso por
teclado/toque. Na reconstrução de uma troca dentro da mesma página, preferir botão nativo; definir
um estado acessível coerente, manter foco no acionador e preservar a posição de leitura. Não
recriar a abertura de abas quebradas como comportamento desejado.

Para texto, validar o par real de primeiro plano e fundo: a WCAG 2.2 exige, em geral, 4,5:1,
ou 3:1 para texto grande. Como referência, `#f1f2f2` sobre `#25265a` e sobre `#004aad` são pares
distintos e devem ser medidos separadamente. A existência de uma paleta chamada alto contraste
não dispensa a verificação de links, foco, imagens com texto e estados interativos.
Referência: [WAI — contraste mínimo](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).

## Validação e manutenção

O levantamento incluiu navegação e cliques nas duas publicações, inspeção de estilos computados
após percorrer as seções, leitura dos dados serializados, conferência do fluxo local nos dois
sentidos e cópia das fontes originais. `evidence.json` guarda amostras, não um espelho do conteúdo
da agenda. Nenhum JSON do backend foi duplicado aqui.

Validação dos arquivos entregues: as 16 faces carregaram no navegador; seus hashes correspondem
aos arquivos de origem. Uma página temporária confirmou o ciclo `standard → high → standard`
nos tokens de banner, badge, atividade, mapa e redes, além da herança de Open Sans. Caminhos locais,
referências entre tokens e links Markdown também foram conferidos. O console dessa página
temporária apresentou apenas a ausência de `favicon.ico`, sem falhas de fontes ou CSS.

Para usar esta referência na futura interface:

1. Conferir normal → alto contraste → normal em banner, agenda, grupos, gincana, mapas e redes.
2. Inspecionar o elemento que realmente pinta: o fundo de uma célula do Canva pode estar em
   uma imagem de fundo gerada, enquanto o `td` informa fundo transparente. Usar metadados e
   aparência juntos; não concluir que um fundo não existe só pela cor computada do `td`.
3. Verificar fontes carregadas, pesos, acentos, caracteres portugueses e fallback offline.
4. Testar desktop, tablet, celular, zoom, Tab e acionamento do controle por teclado, sem
   rolagem horizontal involuntária. Não alterar fontes/tamanho/conteúdo como efeito do tema.
5. Validar estados de foco, links visitados, placeholders e elementos adicionados ao HTML.
6. Ao integrar à home atual, preservar os contratos do carrossel descritos em `AGENTS.md`.

Os testes responsivos e de carrossel pertencem à integração futura: este levantamento não mudou
layout ou comportamento da home. Alterações nos tokens históricos devem atualizar este documento
e registrar se corrigem uma divergência da cópia ou se criam uma decisão visual nova.

## Referências técnicas

As referências do backend orientam a organização do sistema; não fornecem as cores históricas.
Neste levantamento foram consultadas via Playwright as páginas técnicas abaixo:

- [W3C — CSS Custom Properties](https://www.w3.org/TR/css-variables-1/): cascata, herança e
  resolução de variáveis; base para os aliases semânticos.
- [MDN — @font-face](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@font-face):
  arquivos, famílias, pesos, estilos e carregamento de fontes.
- [WAI — Contrast Minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html):
  critérios de contraste de texto.

Para a arquitetura de papéis tipográficos e estados, o [DESIGN do backend](../backend/DESIGN.md)
também reúne Material 3, Fluent 2, Carbon, GOV.UK e DTCG. Essas referências não autorizam substituir
as famílias e cores extraídas do Canva pelas do painel administrativo.

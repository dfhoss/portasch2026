# Sistema de design do frontend

## Escopo

Este documento descreve a identidade visual da home estática do UFFS de Portas Abertas na versão
base `0e6d610`. A interface usa a linguagem visual do projeto Contraste: azul-violeta intenso,
verde-limão, magenta, tipografia pesada e cartões claros para apresentar atividades em andamento.

O documento é a referência para alterações em `index.html` e `styles.css`. A implementação deve
preservar a hierarquia e os contratos de interação, mas pode substituir valores literais por
tokens CSS ao evoluir a folha de estilos.

## Princípios

- **Contraste expressivo:** o banner é o ponto focal; azul-violeta ancora a marca, verde-limão
  destaca títulos e ações, e magenta sinaliza presença/atividade.
- **Estrutura legível:** conteúdo centralizado, cartões com hierarquia clara e largura limitada
  para leitura; efeitos visuais não podem prejudicar o conteúdo.
- **Movimento funcional:** transições e pulso do indicador ao vivo reforçam estado, mas devem
  respeitar `prefers-reduced-motion` quando a animação for ampliada ou reutilizada.
- **Acessibilidade primeiro:** landmarks semânticos, nomes acessíveis nos controles e navegação
  completa por teclado e toque são parte do design, não acabamento.

## Tokens visuais

Use estes valores como referência canônica da versão-base:

| Papel | Token sugerido | Valor |
| --- | --- | --- |
| Fundo da página | `--color-page` | `#f8f8f0` |
| Fundo do banner | `--color-brand` | `#393ce4` |
| Azul do padrão do banner | `--color-brand-soft` | `#4f52e8` |
| Verde-limão de destaque | `--color-accent` | `#e3ff00` |
| Linha de base | `--color-accent-line` | `#c8ff00` |
| Magenta de presença | `--color-live` | `#ed54ce` |
| Superfície de cartão | `--color-surface` | `#ffffff` |
| Texto principal | `--color-text` | `#1a1a2e` |
| Texto secundário | `--color-text-muted` | `#555555` |
| Superfície de tag | `--color-tag-surface` | `#f0f0ff` |

Dimensões importantes:

- conteúdo principal: máximo de `1100px`, com `48px 24px 80px` no desktop;
- cartão: raio de `16px`, borda de `2px`, altura mínima de `260px` e padding aproximado de `22px`;
- controle circular: `44px` no desktop e `38px` até `600px`;
- espaçamento do trilho: `20px`, compartilhado pelo cálculo de deslocamento do JavaScript.

## Tipografia

- Marca e títulos usam sans-serif pesada (`Arial Black`, `Helvetica Neue`, `Arial`) com caixa alta
  e espaçamento compacto.
- Badge e status usam monoespaçada (`Courier New`, `Lucida Console`) para reforçar o caráter
  técnico e facilitar a distinção de rótulos curtos.
- Corpo e localização usam a pilha do sistema; mantenha altura de linha entre `1.4` e `1.6` para
  descrições e não use caixa alta em parágrafos longos.
- Títulos são fluidos com `clamp()` para evitar saltos bruscos entre viewports.

## Componentes

### Banner

O banner ocupa toda a largura e usa altura fluida entre `280px` e `480px`. O padrão de círculos é
decorativo e não recebe foco. A marca central combina o badge “UFFS DE”, o título em duas linhas,
os óculos como imagem decorativa e a assinatura “CONTRASTE” no canto inferior direito. A linha
verde-limão permanece no limite inferior.

### Cartão de atividade

Cada cartão apresenta, nesta ordem: status (`AO VIVO` ou `EM BREVE`), horário, título, local,
descrição e tag. O cartão cresce para preencher a altura da faixa e não deve esconder o texto por
causa de um título mais longo. O hover pode elevar o cartão apenas como reforço secundário; o
estado precisa continuar compreensível sem apontador.

### Carrossel

O carrossel é uma região rotulada com botões anterior/próximo, indicadores em `role="tablist"` e
suporte às setas esquerda/direita. O número de cartões visíveis acompanha os breakpoints:

| Largura | Cartões visíveis | Tratamento |
| --- | ---: | --- |
| acima de `900px` | 3 | faixa ampla com controles laterais |
| `601px`–`900px` | 2 | cartões mais largos e dois itens por página |
| até `600px` | 1 | cartão único e controles reduzidos |

O autoplay percorre os itens em ciclo e o botão próximo volta ao primeiro quando chega ao fim.
Indicadores representam páginas; mudanças no número de cartões devem atualizar tanto os pontos
quanto o limite do índice.

## Responsividade

- Em telas menores que `700px`, os óculos migram para o canto superior direito e a assinatura
  reduz sua distância das bordas.
- Em telas menores que `600px`, reduza o padding do conteúdo para `32px 16px 60px`, use um cartão
  por vez e preserve alvos de toque confortáveis.
- Não introduza rolagem horizontal da página para resolver o carrossel; a rolagem deve ficar
  contida na região do trilho.

## Acessibilidade e movimento

- Mantenha `lang="pt-BR"`, `role="banner"`, título de seção associado por `aria-labelledby`,
  rótulos nos botões e `alt=""` na imagem puramente decorativa dos óculos.
- O foco do carrossel deve ser visível. O teclado precisa alcançar os botões e a região focável;
  setas devem mover a atividade sem alterar o significado do conteúdo.
- Estados “AO VIVO” e “EM BREVE” devem aparecer como texto, nunca somente como cor.
- Ao adicionar animações, inclua uma regra para `@media (prefers-reduced-motion: reduce)` que
  remova pulso e transições não essenciais.

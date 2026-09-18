# Nova identidade do frontend — especificação

> Registro histórico da migração inicial. As decisões posteriores do usuário (fundo claro, banner centralizado, carrossel circular e consolidação documental) estão no [DESIGN único do frontend](../../../frontend/DESIGN.md). Ele prevalece sobre os valores e critérios antigos registrados abaixo.

Data: 2026-09-18. Escopo aprovado pelo pedido do usuário: aplicar DESIGN.md ao frontend atual, usar os banners fornecidos para desktop/celular, renomear assets; executar com worktree, TDD e SDD.

## Objetivo
A home usa a paleta nova de nove cores, fontes reais locais e hero responsivo com imagem integral. O conteúdo, agenda e interação existentes permanecem funcionais.

## Arquitetura
- Criar frontend/static/css/tokens.css como fonte única de primitivas e tokens semânticos da aplicação.
- Mover faces necessárias ao runtime para frontend/static/assets/fonts/ com nomes reais; criar frontend/static/css/fonts.css. O arquivo histórico static/design-old é referência, não dependência de runtime.
- Ordem no head: fonts.css, tokens.css, main.css, schedule.css.
- Consumir os 45 papéis de DESIGN.md; retirar cores antigas literais de componentes e declarações duplicadas da agenda. Cor transparente, currentColor e none não são cores de marca.
- Fontes: Open Sans 400/700 para leitura; Disket Mono 400/700 para headings/mono; Retropix 400 como papel pixel; Garet 400/700 para informações. Não criar peso 900 sintético. Font-display swap e fallbacks.
- CSS de layout atual preservado exceto hero e ajustes mínimos exigidos por fontes/overflow.

## Modos
standard é o modo novo normal. high-contrast e dark continuam como aliases do tema legado já existente, centralizado e documentado como provisório, sem botão novo nem paleta inventada. Não há asset de alto contraste novo: o banner normal continua visível se o tema legado for forçado. DESIGN.md mantém placeholders da identidade futura; o bloco legado não é o preenchimento deles.
Para os pares novos, usar as cores do tema legado existente com função equivalente, para evitar textos/fundos incompatíveis. Nenhum marcador PENDENTE pode entrar em CSS servido.

## Hero e assets
- Renomear apenas frontend/static/assets/images/1dce2337-9bd4-40de-bc0d-6bb92b9a038c.jpg para hero-desktop.jpg (5938 × 1250).
- Renomear frontend/static/assets/images/Site banner 9 x 16.png para hero-mobile.png (1080 × 437).
- Preservar bytes originais; não recodificar/cortar imagens.
- Usar picture com source media="(max-width: 600px)" para mobile; img fallback desktop. A imagem deve ter width/height intrínsecos corretos e estilos width:100%, height:auto, display:block. Source pode informar dimensões também para reservar razão mobile.
- Remover composição antiga do header (badge/título visual/óculos/logo/padrões/linha), sem sobrepor marca duplicada à imagem.
- Manter h1 semanticamente disponível, com classe visualmente oculta, e alt com Campus Chapecó, data e horário presentes na arte; evitar duplicar o título no alt.
- Não criar nova semântica de data do backend a partir da imagem.
- PNG horizontal anterior continua como referência não selecionada pelo hero.
- Atualizar referências aos arquivos renomeados e documentação que ainda chamava o compacto de candidato móvel: usuário confirmou finalidade celular.

## Componentes
Migrar body, banner, cards do carrossel, badges, controles, indicadores, agenda, summaries, tags, estados finalizados, regulamento, links, SVG e pseudo-elementos para papéis de tokens. Links e foco devem permanecer visíveis. Usar pares action, selected, tag e status em vez de assumir que brand sempre é cor de texto ou que accent sempre é texto sobre marca.

## Restrições globais
- Somente frontend, specs/plans e testes relacionados; não modificar backend/db/participants.json nem outros dados.
- Sem build, bundler, package.json ou dependência runtime nova.
- lang="pt-BR", landmarks, rótulos, foco, teclado e toque preservados.
- Carrossel: 3 cartões acima de 900px, 2 de 601px a 900px, 1 até 600px; gap 20px; autoplay 5s; debounce resize 150ms; swipe maior que 50px.
- Sem alterar scripts de negócio/carrossel salvo correção indispensável demonstrada por teste e registrada.
- Sem rolagem horizontal involuntária em 390, 768 e 1440px.
- Fontes e imagens locais, nomes reais, caminhos relativos.
- Alto contraste novo permanece pendente; não adicionar toggle novo.
- Preservar mudanças não relacionadas do checkout principal.

## Testes e aceite
Python unittest + Playwright instalado no ambiente dev existente (backend/.venv), sem instalar biblioteca nova no frontend. Cada tarefa implementa primeiro teste de comportamento renderizado, observa RED por expectativa não satisfeita, implementa e registra GREEN. Servidor temporário HTTP usa a raiz do worktree, para servir os JSONs reais; deve ser encerrado pelo harness.
Task 1: cores computadas, fontes carregadas e herança em componentes, estados selecionado/finalizado e pares do tema legado, ausência de tokens pendentes em CSS runtime.
Task 2: currentSrc desktop/mobile, dimensões/proporção, ausência de clipping/overflow, um h1, imagens carregadas, teclado e swipe do carrossel, resize e erro de carregamento de agenda com página utilizável.
Usar dados efetivamente fornecidos pela agenda ou interceptação explícita para estado de erro; não criar cópia da agenda.
Inspeção visual complementar via MCP Playwright em desktop/tablet/celular. Não afirmar equivalência ao alto contraste novo.

## Documentação
Atualizar frontend/DESIGN.md para regras efetivas e frontend/README.md para carregamento/fontes/testes/hero; atualizar DESIGN.md como implementado no normal, com referências corretas e pendências mantidas.
Registrar evidência TDD e revisão em relatórios SDD; criar commits locais na branch isolada, sem merge/push nesta etapa.

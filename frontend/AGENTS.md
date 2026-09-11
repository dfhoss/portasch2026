# Diretrizes do frontend

O frontend é uma página estática do UFFS de Portas Abertas. Preserve a identidade visual do
Contraste, o funcionamento do carrossel e o acesso por teclado/toque ao alterar a home.

## Comandos de desenvolvimento

- `py -m http.server 4173 --directory frontend` — serve a página localmente; abra
  `http://localhost:4173/`.
- `python -m http.server 4173 --directory frontend` — alternativa quando `py` não estiver
  disponível.
- Não há etapa de build nem gerenciador de dependências no frontend legado; teste os arquivos
  estáticos diretamente no navegador.

## Regras de design

- Leia `DESIGN.md` antes de modificar a interface. Cores, tipografia, espaçamento, bordas e
  comportamento responsivo devem continuar coerentes com os tokens documentados.
- Preserve `lang="pt-BR"`, landmarks semânticos, rótulos acessíveis e foco visível. Não dependa
  apenas de cor, hover ou movimento para comunicar estado.
- Mantenha os assets relativos à página. Não renomeie arquivos em `assets/` sem atualizar todos
  os caminhos que dependem dos nomes originais.
- Os arquivos servidos pela página ficam em `static/`: CSS em `static/css/`, JavaScript em
  `static/js/`, dados em `static/data/`, assets em `static/assets/` e componentes em
  `static/complete-program/`.

## Armadilhas e pontos de atenção

### Carrossel

- A quantidade de cartões visíveis é 3 acima de 900px, 2 entre 601px e 900px e 1 até 600px;
  qualquer mudança no CSS precisa manter essa mesma divisão no JavaScript.
- O deslocamento usa a largura real do primeiro cartão mais um gap fixo de `20px`; alterar o
  gap somente no CSS desalinha a navegação.
- O autoplay chama `next()` a cada 5 segundos e reinicia após controles, teclado ou swipe. O
  `resize` recria os indicadores após 150ms; preserve esse debounce para evitar estados
  intermediários.
- O swipe só navega quando a diferença horizontal ultrapassa 50px. Não transforme um toque curto
  em navegação.
- O carrossel inicia o timer automaticamente e não pausa sozinho em foco ou hover; qualquer
  mudança nesse comportamento deve incluir uma decisão explícita de acessibilidade.

### Conteúdo e integração

- A versão-base documentada aqui contém conteúdo estático no HTML. Dados dinâmicos ou integração
  com a API exigem manter a página utilizável quando a rede falhar.
- A agenda completa adicionada em commits posteriores possui documentação própria em
  `static/complete-program/`; não misture seus tokens ou contratos com a home legada sem atualizar
  `DESIGN.md`.

## Validação

- Teste em desktop, tablet e celular; confirme que não há rolagem horizontal involuntária.
- Use Tab e as setas esquerda/direita no carrossel e teste o gesto de swipe em dispositivo móvel.
- Verifique console, carregamento das imagens e estados inicial/final dos botões após redimensionar
  a janela.
- Ao alterar comportamento ou estrutura, atualize `README.md` e `DESIGN.md` somente quando a
  regra deixar de ser inferível pelo código ou passar a ser uma decisão visual/operacional.

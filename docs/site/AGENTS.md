# Diretrizes do frontend

O frontend é uma página estática do UFFS de Portas Abertas. Preserve a identidade visual do
Contraste, o funcionamento do carrossel e o acesso por teclado/toque ao alterar a home.

## Comandos de desenvolvimento

- Na raiz do projeto (`portasch2026/`), execute `uv --directory frontend run python -m http.server 4187 --bind 127.0.0.1 --directory ..`.
  O `uv` executa na pasta `frontend/`, sem exigir `cd` no terminal.
  Abra `http://127.0.0.1:4187/frontend/`; a raiz servida inclui os JSONs de `backend/db/`.
- Com Live Server, sirva a raiz do repositório e abra `/frontend/`: a agenda também precisa
  acessar `backend/db/`. A presença de conteúdo na tela não comprova que os JSONs carregaram.

## Regras de design

- Leia `static/site/DESIGN.md` antes de modificar a interface e use os tokens documentados.
- Preserve `lang="pt-BR"`, landmarks semânticos, rótulos acessíveis e foco visível. Não dependa
  apenas de cor, hover ou movimento para comunicar estado.
- Mantenha assets relativos à página; renomeações exigem atualizar todas as referências.

## Armadilhas e pontos de atenção

### Carrossel

- Breakpoints e gap do trilho são acoplados entre CSS e JavaScript; atualize ambos juntos.
  Preserve a medição fracionada da largura dos cartões para evitar desvios em zoom.
- O timeout de conclusão deve acompanhar a duração variável da transição; um valor fixo
  pode interromper o loop antes do reposicionamento invisível.
- Preserve o debounce de resize e a distinção entre toque curto e swipe.
- Mudanças na política de autoplay em foco/hover exigem decisão explícita de acessibilidade.
- Cópias `data-carousel-clone` não são atividades reais: exclua-as de contagens, foco e leitura assistiva.

### Conteúdo e integração

- O backend define o formato e os IDs da agenda; não crie cópias locais dos dados no frontend.
- Preserve a página utilizável na falha de rede. Em `schedule.js`, falhas em qualquer um dos três
  JSONs mantêm o HTML inicial silenciosamente: confira as respostas de rede, não apenas o console.
- A normalização usa `GUIDING_AXES` de `schedule.js`, embora carregue `knowledge_axes.json`;
  alterar apenas esse JSON não atualiza a lista de eixos exibida.

## Validação

- Teste desktop, tablet, celular e zoom fracionado: sem overflow horizontal ou recorte dos cartões.
- Confira Tab, setas, swipe curto/longo, loop nos dois sentidos e controles após resize.
- Verifique imagens, console, respostas dos JSONs e fallback com falha de rede.
- Atualize `docs/site/README.md` e `static/site/DESIGN.md` para decisões visuais/operacionais; mantenha aqui apenas
  restrições e armadilhas que não sejam rapidamente inferíveis pelo código.

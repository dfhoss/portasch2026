# Frontend — UFFS de Portas Abertas

Frontend estático da página pública do UFFS de Portas Abertas. A versão-base (`0e6d610`) apresenta
um banner da identidade Contraste e a seção “Rolando agora”, com cartões de atividades em um
carrossel responsivo.

## Executar localmente

Na pasta `frontend/`:

```powershell
uv run python -m http.server 4187 --bind 127.0.0.1 --directory ..
```

Abra <http://127.0.0.1:4187/frontend/>. O comando requer `uv` disponível no PATH e serve
a raiz do repositório para disponibilizar também os JSONs de `backend/db/`.

Não há `package.json`, bundler ou dependências de frontend nessa versão; o navegador carrega
`index.html`, `static/css/main.css`, `static/css/schedule.css`, `static/js/carousel.js`, `static/js/schedule.js` e os assets relativos diretamente. A programação é lida de
`backend/db/schedule.json`, `backend/db/knowledge_axes.json` e `backend/db/locations.json`, que são
as fontes de verdade do backend.

### Identidade e fontes

`static/css/fonts.css` e `static/css/tokens.css` são carregados antes das folhas de componentes.
As faces locais (Open Sans, Disket Mono, Retropix e Garet) usam `font-display: swap`, sem CDN.
Os papéis semânticos e os aliases provisórios dos temas `high-contrast`/`dark` ficam centralizados
em `tokens.css`; a identidade nova de alto contraste continua pendente.

O hero usa as artes integrais `static/assets/images/hero-desktop.jpg` e `hero-mobile.png` via
`picture`, com breakpoint móvel em 600px e sem recorte ou rolagem horizontal.
O banner fica centralizado com largura máxima de 1100px e acompanha o zoom até o limite da tela.

### Testes automatizados

Com o ambiente Playwright disponível em `backend/.venv`:

```powershell
..\backend\.venv\Scripts\python.exe -m unittest discover -s frontend/tests -p "test_*.py" -v
```

## Organização

`DESIGN.md` é a única referência de design do frontend: reúne a identidade atual, regras de
interação, referências históricas e pendências de alto contraste. O fundo normal usa `#f1f2ec`
e os cartões mantêm `#ffffff`.

| Caminho | Responsabilidade |
| --- | --- |
| `index.html` | Estrutura semântica da home e conteúdo dos cartões |
| `static/css/` | Folhas de estilo da página |
| `static/js/` | Scripts e módulos JavaScript |
| `static/assets/images/` | Imagens usadas pela página |
| `archive/legacy/` | Backups antigos, fora do carregamento da aplicação |
| `DESIGN.md` | Tokens e regras visuais/acessíveis |
| `AGENTS.md` | Regras operacionais para manutenção por agentes |

## Comportamento do carrossel

- 3 cartões são exibidos acima de `900px`, 2 entre `601px` e `900px`, e 1 até `600px`.
- O autoplay avança a cada 5 segundos e reinicia depois de navegação manual.
- Controles, indicadores, setas e autoplay usam as mesmas páginas de 3/2/1 cartões. A última
  página pode repetir cartões da anterior para não deixar espaços vazios.
- A navegação é circular nos dois sentidos, com passagem contínua entre última e primeira
  página. Os controles só ficam desabilitados quando todos os cartões cabem em uma página.
- Cópias nas extremidades servem apenas à animação e usam `aria-hidden` e `inert`.
- Setas esquerda/direita e swipe horizontal navegam entre páginas; o swipe exige mais de
  50px de deslocamento.
- O resize é processado após 150ms para recriar os indicadores e recalcular o deslocamento.
- Com movimento reduzido, a troca é imediata. O autoplay mantém o comportamento existente.

## Validação manual

1. Abra a página em desktop e redimensione para tablet e celular.
2. Confirme que imagens e estilos carregam sem erros no console.
3. Use Tab para alcançar os controles e as setas para navegar.
4. Verifique a bolinha selecionada a cada página e o retorno contínuo nos dois sentidos.
5. Teste swipe em um dispositivo móvel ou no modo responsivo do navegador.

Para alterações visuais ou de interação, consulte [`DESIGN.md`](./DESIGN.md) e registre em
[`AGENTS.md`](./AGENTS.md) somente regras operacionais que não possam ser descobertas rapidamente
no código.

## Evolução da branch

A programação completa é renderizada pela própria home e usa o script `static/js/schedule.js` apenas
para lógica de interação e transformação. Os dados são lidos diretamente de `backend/db/`: agenda,
eixos de conhecimento e locais. O formato do backend dita o contrato de funcionamento do frontend;
não replique dados de negócio dentro dos arquivos JavaScript.

## Referências técnicas

Para decisões de UI, consulte a seção [Referências para implementação](./DESIGN.md#referências-para-implementação)
no `DESIGN.md`. Ela reúne as referências usadas pelo backend para tipografia, botões, estados,
layout, overflow, tokens CSS e acessibilidade visual:

- Material Design 3, Fluent 2, Carbon e GOV.UK para padrões de componentes e hierarquia;
- W3C e Design Tokens Community Group para propriedades personalizadas e tokens;
- MDN para `var()`, Flexbox e `overflow`.

Antes de introduzir um novo padrão visual, verifique primeiro se ele pode ser expresso pelos
tokens e regras já documentados no `DESIGN.md`.

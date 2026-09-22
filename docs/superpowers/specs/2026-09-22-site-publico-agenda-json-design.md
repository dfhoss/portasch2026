# Site público — agenda orientada por JSON e somente leitura

Data: 2026-09-22  
Status: aprovado para especificação; a implementação depende de plano posterior.

## Objetivo

Fazer o site público consumir a agenda persistida nos JSONs do backend como sua única fonte
de conteúdo de programação. O navegador não deverá manter uma cópia da agenda no HTML, não
deverá gravar arquivos em `db/` e não deverá usar a API administrativa para editar dados.

O painel `/admin` permanece separado: ele continua sendo a interface autenticada que edita os
catálogos por meio da API existente. Esta especificação trata somente de `static/site/` e da
entrega pública, somente leitura, dos JSONs necessários.

## Contexto e problema

O HTML público atualmente contém uma cópia extensa da programação e o carrossel inicial usa
atividades que não estão em `db/schedule.json`. O `schedule.js` já tenta buscar
`/db/schedule.json`, mas o mount público atual serve apenas `static/site/`; portanto, a busca
não alcança os arquivos reais do backend. Além disso, a normalização atual mantém eixos
codificados no JavaScript e não usa integralmente os catálogos recebidos.

Essa combinação permite que o HTML, o JavaScript e os JSONs apresentem agendas divergentes.
Também mistura duas responsabilidades diferentes: o site público precisa exibir dados, enquanto
o painel administrativo precisa validar e persistir alterações.

## Decisão

Será criada uma entrega pública de arquivos JSON, com leitura restrita a uma lista conhecida,
em `GET /db/{file_name}`. O site buscará somente:

- `GET /db/schedule.json`;
- `GET /db/knowledge_axes.json`;
- `GET /db/locations.json`.

Essa entrega não será um endpoint de edição e não ficará sob o prefixo `/api`. Ela deve retornar
os arquivos reais apontados pelas configurações do processo, resolvendo os caminhos no momento
de cada requisição. O arquivo `db/users.json` e qualquer outro caminho não listado nunca serão
publicados.

O HTML passará a conter apenas o shell sem dados persistidos. `schedule.js` carregará os três
JSONs, derivará as visões por turno e por eixo e renderizará a programação completa. O carrossel
“Rolando agora” também será alimentado por atividades reais da agenda. A inicialização do
carrossel será idempotente e ocorrerá depois que os cards tiverem sido montados.

## Alternativas descartadas

### Copiar os JSONs para `static/site/`

Descartada porque cria duas fontes de verdade, não acompanha `SCHEDULE_PATH`,
`LOCATIONS_PATH` e `KNOWLEDGE_AXES_PATH` em deployments isolados e pode expor dados antigos.

### Usar `GET /api/schedule` no site público

Descartada porque acopla uma página pública à fronteira autenticada do painel, mistura o
contrato de leitura pública com o fluxo administrativo e não resolve a necessidade de impedir
escritas pelo frontend.

### Manter o HTML como fallback completo

Descartada para a agenda: um fallback com todos os cards seria outra cópia persistida. Em caso
de falha dos JSONs, o shell da página, o hero, o regulamento, o mapa e os demais conteúdos
estáticos continuam utilizáveis; a agenda permanece vazia sem exibir uma mensagem de erro
intrusiva. Um `<noscript>` orienta quem estiver sem JavaScript.

## Arquitetura e fluxo

```mermaid
flowchart LR
    Browser[site público] -->|GET /db/*.json| PublicData[entrega pública somente leitura]
    PublicData -->|caminho resolvido por requisição| Json[db/*.json]
    Browser -->|HTML, CSS, JS e imagens| Site[static/site/]
    Admin[static/admin/] -->|API autenticada| Api[/api/*]
    Api --> Clients[clients/]
    Clients -->|persistência atômica| Json
```

### Entrega pública dos JSONs

O módulo de site deverá oferecer uma função de resolução com allowlist explícita:

- `schedule.json` usa `clients.schedule.get_schedule_path()`;
- `locations.json` usa `clients.locations.get_locations_path()`;
- `knowledge_axes.json` usa `clients.knowledge_axes.get_knowledge_axes_path()`.

Os factories são chamados dentro do handler, nunca avaliados uma única vez no import. O
handler deve rejeitar nomes fora da allowlist com `404`, verificar que o arquivo existe e é
regular, responder com `application/json` e não revelar caminhos locais em mensagens de erro.
O cache deve permitir revalidação (`Cache-Control: no-cache` ou equivalente), pois uma alteração
feita no painel deve aparecer no próximo carregamento do site.

O handler não aceita corpo, não implementa `PUT`, `POST`, `PATCH` ou `DELETE` e não chama os
clients de gravação. A rota não precisa aparecer na documentação OpenAPI administrativa.

### Leitura e normalização no navegador

`schedule.js` deverá expor funções pequenas e testáveis para:

1. carregar os três documentos em paralelo, exigindo `response.ok` e JSON válido;
2. localizar a seção `complete-program` sem alterar o documento original;
3. criar mapas de eixos e locais a partir dos catálogos;
4. manter nomes de locais como texto seguro, juntando vários locais com ` · `;
5. derivar turnos por sobreposição de intervalos;
6. derivar eixos usando os IDs do JSON, sem `GUIDING_AXES` ou `COURSE_AXIS_MAP` fixos;
7. preservar todos os grupos, inclusive grupos sem eixo ou com referência desconhecida, em uma
   categoria textual equivalente a “Sem eixo”;
8. calcular o estado temporal com `America/Sao_Paulo` e exibir sempre um rótulo textual:
   `AO VIVO`, `EM BREVE` ou `FINALIZADA`;
9. renderizar títulos, descrições, horários, locais e links usando `textContent` e atributos
   DOM, nunca interpolação de HTML com conteúdo vindo dos JSONs.

O modo por turno mostra os grupos que têm sessões sobrepostas ao intervalo do turno. O modo por
eixo mostra cada grupo sob o nome vindo de `knowledge_axes.json`; grupos nulos ou não
encontrados não podem desaparecer. O estado de finalização deve continuar sendo aplicado aos
cards sem depender apenas de cor.

O carrossel seleciona no máximo cinco atividades únicas. No dia do evento, prioriza atividades
ao vivo e depois as próximas; fora do dia do evento, usa as próximas atividades para o evento
futuro ou as últimas atividades para o evento já encerrado. A ordem original do JSON desempata
itens equivalentes. Os textos dos cards, horários e locais devem sempre vir do documento
carregado; não haverá títulos fictícios nem tags inventadas no HTML.

`carousel.js` deverá oferecer uma inicialização idempotente para o trilho montado pelo
`schedule.js`, preservando o contrato existente de breakpoints, gap, medição fracionada,
teclado, toque, loop, resize, autoplay e `prefers-reduced-motion`. Cópias de loop continuarão
marcadas com `data-carousel-clone`, `aria-hidden="true"` e `inert`.

### Shell e falha de carregamento

`static/site/index.html` manterá:

- `lang="pt-BR"`, landmarks, hero, regulamento, mapas e demais conteúdos estáticos;
- a seção `complete-program` com título, seletor acessível e mount vazio;
- o carrossel com controles e trilho vazio enquanto os dados não chegam;
- um `<noscript>` informando que JavaScript é necessário para consultar a programação;
- nenhum título, descrição, horário, local, eixo, ID ou card de atividade copiado de `db/`.

O estado inicial usará `aria-busy="true"` somente durante o carregamento. Em sucesso, o
script atualiza o shell e marca os mounts como não ocupados. Em falha de rede, HTTP ou parse,
o script encerra silenciosamente, remove o estado ocupado e deixa o conteúdo estático utilizável;
não fará retry infinito, não exibirá stack trace e não tentará usar `/api` como fallback.

## Contrato de não edição pelo site público

O contrato deve ser explícito e verificável:

- `static/site/js/` só poderá fazer requisições `GET` aos três arquivos públicos;
- nenhum script do site poderá chamar `/api/schedule`, `/api/locations` ou
  `/api/knowledge-axes`;
- nenhum script do site poderá emitir método mutável para `/db/` ou `/api/`;
- não haverá formulário, botão ou estado local para editar a agenda pública;
- alterações continuam pertencendo ao painel autenticado, que usa a API e a persistência
  atômica dos clients existentes;
- `static/site/DESIGN.md` será a documentação ativa dessa fronteira, sem substituir a
  documentação de arquitetura nem o contrato do painel.

## Acessibilidade e contratos visuais

A implementação deverá preservar os contratos já vigentes em `static/site/DESIGN.md`:

- tokens semânticos continuam sendo a fonte das cores, bordas, foco e estados;
- status de atividade aparecem como texto além de qualquer cor;
- headings, `aria-labelledby`, `role="radiogroup"`, `role="radio"`, `aria-checked`,
  `aria-busy` e `aria-live` permanecem coerentes após cada renderização;
- foco de teclado continua visível nos seletores, `details`, setas e indicadores;
- controles mantêm alvos de toque, responsividade e ausência de overflow em 390px, 768px e
  1440px;
- a troca de visão não perde grupos abertos, foco ou estado selecionado quando isso for
  possível sem reintroduzir dados estáticos;
- clones do carrossel não entram em contagem, foco ou leitura assistiva;
- novas transições respeitam `prefers-reduced-motion`;
- não se alteram tokens nem componentes de `static/admin/`; se uma validação tocar o painel,
  ela apenas confirmará que a fronteira administrativa continua intacta conforme
  `static/admin/DESIGN.md`.

## Escopo

### Incluído

- nova entrega pública read-only para os três JSONs;
- reescrita de `static/site/js/schedule.js` e adaptação de `carousel.js`;
- remoção da cópia de agenda e dos cards fictícios de `static/site/index.html`;
- testes do handler público, da normalização/renderização e dos fluxos no navegador;
- atualização de `static/site/DESIGN.md`, `ARCHITECTURE.md` e `README.md`;
- preservação dos formatos dos JSONs e da API administrativa existente.

### Fora do escopo

- alterar o schema de `schedule.json`, `locations.json` ou `knowledge_axes.json`;
- mudar o CRUD, autenticação ou autorização de `/admin`;
- permitir edição, exportação ou upload pelo site público;
- criar bundler, `package.json`, dependência de runtime ou cópia gerada dos JSONs;
- substituir a identidade visual, os assets do hero ou o layout do regulamento;
- criar uma nova identidade de alto contraste ou ativar placeholders existentes.

## Estratégia de testes

Os testes devem provar tanto o comportamento quanto a fronteira de segurança:

1. **Rota pública:** verifica que os três arquivos configurados são entregues, que nomes não
   permitidos retornam `404`, que `users.json` não é exposto e que as configurações são lidas
   no momento da chamada.
2. **JavaScript:** cobre normalização dos catálogos, grupos sem eixo, múltiplos locais,
   intervalos nos limites dos turnos, estados temporais, seleção do carrossel e falhas de
   resposta/parse. O teste deve observar uma execução vermelha antes da implementação e verde
   depois dela.
3. **Contrato de rede no navegador:** carrega o site com os JSONs reais ou fixture explicitamente
   interceptada, confirma que um título existente no `db/schedule.json` aparece e que os cards
   fictícios atuais não aparecem. Registra as requisições e garante ausência de métodos mutáveis
   e de chamadas `/api` pelo site público.
4. **Falha de rede:** aborta os JSONs, confirma que hero, regulamento, mapa, headings e
   estrutura da página permanecem disponíveis e que não há erro de aplicação no console.
5. **Regressão visual e de interação:** executa a suíte existente para desktop, tablet e
   celular, incluindo teclado, toque, resize, loop, foco, zoom fracionado, imagens, fontes,
   ausência de overflow e movimento reduzido.
6. **Qualidade do repositório:** executa `uv run pytest`, `uv run ruff check .`,
   `uv run ruff format --check .` e `uv run ty check`, removendo os artefatos temporários
   previstos em `tests/conftest.py`.

## Critérios de aceite

- A programação pública renderizada corresponde ao JSON configurado, sem cópia de dados de
  agenda no HTML ou em um segundo arquivo de runtime.
- O site público funciona sem autenticação e não utiliza a API administrativa para leitura ou
  escrita da agenda.
- Apenas os três JSONs públicos são entregues; usuários, hashes e outros arquivos não são
  acessíveis por essa rota.
- O painel autenticado continua podendo editar e persistir os JSONs pela API existente.
- Turnos, eixos, locais, horários, status, foco, teclado, toque e responsividade permanecem
  funcionais.
- Falhas de carregamento não apagam o restante da página nem exibem erro técnico ao público.
- A decisão de fonte de verdade e de não edição pelo site está registrada em
  `static/site/DESIGN.md` e refletida em `ARCHITECTURE.md` e `README.md`.

## Tarefas de implementação previstas

1. Criar a entrega pública allowlisted dos JSONs e seus testes, sem expor outros arquivos.
2. Escrever os testes vermelhos da normalização e da renderização orientadas pelos dados.
3. Reescrever `schedule.js`, incluindo a programação completa, estados e carrossel dinâmico.
4. Simplificar `index.html`, adaptar a inicialização de `carousel.js` e preservar os contratos
   de acessibilidade e responsividade.
5. Atualizar `static/site/DESIGN.md`, `ARCHITECTURE.md`, `README.md` e os testes de navegador.
6. Executar a suíte completa, revisar o diff e registrar evidências de verificação.
7. **Revisar contratos de design** — comparar a implementação com cada contrato aplicável de
   `static/site/DESIGN.md` e confirmar que `static/admin/DESIGN.md` não foi alterado nem teve
   sua fronteira violada; revisar tokens semânticos, ícones, acessibilidade, foco,
   responsividade e animações reduzidas, registrar as evidências e concluir esta tarefa antes
   do commit final.


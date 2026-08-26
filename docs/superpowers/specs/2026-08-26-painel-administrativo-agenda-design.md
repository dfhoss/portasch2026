# Painel administrativo da agenda

## Objetivo

Criar um painel administrativo em HTML, CSS e JavaScript puro, servido pelo FastAPI e
independente do frontend público. O painel permitirá que uma pessoa autenticada edite a
programação, os locais e os eixos de conhecimento usados em `backend/db/schedule.json`.

O frontend público continuará consumindo `schedule.json` no formato atual. A implementação não
modificará a pasta `frontend/`.

## Escopo

O painel permitirá:

- autenticar com o fluxo JWT existente;
- editar a data, a versão, as seções, os grupos, as atividades e as sessões da agenda;
- cadastrar, renomear e excluir locais;
- cadastrar, renomear e excluir eixos de conhecimento;
- selecionar locais nas sessões e eixos nos grupos;
- salvar um rascunho completo após validação do backend.

O sistema considera apenas uma pessoa editando por vez. Controle de concorrência, histórico de
versões e resolução de conflitos não fazem parte deste escopo.

## Arquitetura

O painel será uma aplicação sem processo de build, composta por arquivos estáticos mantidos no
backend:

- `backend/static/admin/index.html`: estrutura do login e do editor;
- `backend/static/admin/admin.css`: estilos isolados do painel;
- `backend/static/admin/admin.js`: autenticação, navegação, rascunho e chamadas à API;
- `backend/routes/admin.py`: entrega da página administrativa;
- `backend/routes/schedule.py`: API autenticada da programação;
- `backend/routes/locations.py`: API autenticada dos locais;
- `backend/routes/knowledge_axes.py`: API autenticada dos eixos;
- `backend/clients/schedule.py`: leitura, validação e gravação da agenda;
- `backend/clients/locations.py`: leitura e gravação dos locais;
- `backend/clients/knowledge_axes.py`: leitura e gravação dos eixos;
- `backend/db/locations.json`: catálogo de locais;
- `backend/db/knowledge_axes.json`: catálogo de eixos.

O `backend/app.py` registrará os novos roteadores e servirá somente os recursos estáticos do
painel. As responsabilidades seguirão o fluxo existente: composição em `app.py`, HTTP em
`routes/` e persistência em `clients/`.

## Autenticação

A rota `/admin` exibirá inicialmente o formulário de login. O formulário enviará as credenciais
ao endpoint `/auth/token` existente. O token ficará apenas em `sessionStorage`, portanto será
descartado ao encerrar a sessão do navegador.

Antes de mostrar o editor, o JavaScript validará o token em `/auth/users/me/`. Todas as APIs de
agenda, locais e eixos usarão `CurrentTokenData` e responderão com `401` para chamadas sem token
válido. Ao receber `401`, o painel descartará o token e voltará ao formulário de login.

O documento HTML e seus recursos estáticos não conterão dados administrativos. A proteção dos
dados e das alterações ocorrerá nas APIs autenticadas.

## Interface administrativa

A interface seguirá o layout aprovado no protótipo:

- navegação lateral para Programação, Locais, Eixos de conhecimento e Minha conta;
- lista de seções ao lado da programação;
- grupos expansíveis e atividades abertas individualmente em formulário;
- sessões editáveis com início, fim e seleção de local;
- cadastros de locais e eixos em telas simples;
- ações com resposta visual, confirmações para exclusões e mensagens de erro claras.

O painel será responsivo e utilizável com teclado. Campos terão rótulos associados, mensagens de
erro serão textuais e o foco será direcionado ao formulário ou erro relevante.

## Modelo da agenda

O formato de `schedule.json` será preservado. O painel editará os campos já presentes:

- `version` e `eventDate`;
- `sections` com `id`, `title`, `description` e `groups`;
- grupos com `id`, `title`, `knowledgeAxis` opcional e `items`;
- atividades com `id`, `title`, `description`, `sessions` e `link`;
- sessões com `startTime`, `endTime` e `location`.

Campos opcionais continuarão opcionais. As sessões não ganharão ID. IDs de novas seções, grupos e
atividades serão gerados pelo backend, não serão exibidos no formulário e evitarão colisões com
registros existentes. Os IDs atuais serão preservados.

## Locais

`locations.json` terá um catálogo simples:

```json
{
  "locations": [
    {
      "id": "loc-001",
      "name": "Bloco A - Sala 105"
    }
  ]
}
```

O usuário informará somente o nome. O backend gerará IDs sequenciais no formato `loc-NNN`, sem
reutilizar IDs removidos. A carga inicial conterá os nomes únicos encontrados nas sessões atuais
de `schedule.json`, preservando inclusive locais especiais e nomes compostos.

O `schedule.json` continuará armazenando o nome no campo `location`, e não o ID. Ao renomear um
local, o backend atualizará as ocorrências que correspondam exatamente ao nome anterior. A
exclusão de um local em uso será recusada e indicará as atividades que ainda o referenciam.

## Eixos de conhecimento

`knowledge_axes.json` conterá os eixos disponíveis:

```json
{
  "knowledgeAxes": [
    {
      "id": "saude-e-bem-estar",
      "name": "Saúde e bem-estar"
    }
  ]
}
```

O usuário informará somente o nome. O backend gerará e ocultará o ID. Grupos poderão ficar sem
eixo, como já ocorre com Programação cultural e Equipes participantes.

Os identificadores ingleses existentes serão migrados para estes termos em português:

- `general` para `geral`;
- `agriculture-forestry-fisheries-and-veterinary` para
  `agricultura-silvicultura-pesca-e-veterinaria`;
- `business-administration-and-law` para `administracao-negocios-e-direito`;
- `computing-and-ict` para `computacao-e-tecnologia-da-informacao`;
- `education` para `educacao`;
- `arts-and-humanities` para `artes-e-humanidades`;
- `engineering-manufacturing-and-construction` para `engenharia-industria-e-construcao`;
- `natural-sciences-mathematics-and-statistics` para
  `ciencias-naturais-matematica-e-estatistica`;
- `health-and-welfare` para `saude-e-bem-estar`;
- `social-sciences-communication-and-information` para
  `ciencias-sociais-comunicacao-e-informacao`.

O frontend público deverá consumir esses valores em português. Depois da migração, renomear o
nome visível de um eixo não alterará seu ID. A exclusão de um eixo em uso será recusada.

## Fluxo de edição e persistência

Após autenticar, o navegador carregará agenda, locais e eixos pelas APIs. As alterações serão
mantidas como rascunho no navegador até a ação explícita de salvar.

Antes de persistir, o backend validará o documento completo, incluindo:

- campos obrigatórios e data no formato esperado;
- unicidade dos IDs;
- horário inicial anterior ao horário final;
- locais cadastrados para todas as sessões que possuam local;
- eixos cadastrados para todos os grupos que possuam eixo;
- estrutura compatível com o contrato de `schedule.json`.

Os clientes de persistência escreverão primeiro em um arquivo temporário no mesmo diretório,
forçarão a conclusão da escrita e substituirão o arquivo de destino de forma atômica. Se a
validação ou a escrita falhar, o JSON anterior permanecerá intacto.

As operações que afetam dois arquivos, como renomear um local e atualizar a agenda, validarão
ambos antes de escrever. Como JSON não oferece transação entre arquivos, a implementação manterá
cópias temporárias dos conteúdos anteriores e fará restauração imediata se a segunda substituição
falhar. Erros de restauração serão registrados com nível crítico e informados como falha de
persistência, sem afirmar sucesso ao cliente.

## API

As rotas administrativas usarão modelos Pydantic explícitos:

- `GET /admin/api/schedule`: obter a agenda;
- `PUT /admin/api/schedule`: substituir a agenda completa após validação;
- `GET /admin/api/locations`: listar locais;
- `POST /admin/api/locations`: criar um local;
- `PUT /admin/api/locations/{location_id}`: renomear um local e propagar seu nome;
- `DELETE /admin/api/locations/{location_id}`: excluir um local que não esteja em uso;
- `GET /admin/api/knowledge-axes`: listar eixos;
- `POST /admin/api/knowledge-axes`: criar um eixo;
- `PUT /admin/api/knowledge-axes/{axis_id}`: renomear um eixo sem alterar seu ID;
- `DELETE /admin/api/knowledge-axes/{axis_id}`: excluir um eixo que não esteja em uso.

Erros de entrada retornarão `422`; referências ou exclusões inválidas retornarão `409`; recursos
inexistentes retornarão `404`; falta de autenticação retornará `401`; falhas inesperadas de
persistência retornarão `500`. As respostas de erro terão uma mensagem apropriada para exibição
no painel e, quando aplicável, a lista de referências que impedem a operação.

## Testes

A estratégia combinará testes de API com testes de navegador.

`pytest` e `TestClient` usarão diretórios temporários e cobrirão:

- acesso sem JWT e com JWT válido;
- leitura e substituição validada da agenda;
- criação, renomeação e exclusão de locais e eixos;
- geração automática e unicidade de IDs;
- migração completa dos eixos para português;
- recusa de referências inválidas e exclusões em uso;
- propagação de nomes de locais;
- preservação ou restauração dos arquivos em falhas de validação e escrita;
- entrega básica da página administrativa.

Playwright para Python executará os fluxos completos em navegador real:

- login válido e inválido;
- retorno ao login quando a sessão não for válida;
- navegação entre Programação, Locais, Eixos e Minha conta;
- criação e edição de atividades e sessões;
- cadastro e seleção de locais;
- cadastro e seleção de eixos;
- mensagens de validação e confirmações;
- bloqueio de exclusões em uso;
- salvamento seguido de recarregamento dos dados.

Os testes sempre apontarão para cópias temporárias dos JSONs e nunca alterarão os dados reais do
repositório.

## Critérios de aceite

- `/admin` oferece login e editor sem depender da pasta `frontend/`.
- Nenhum dado ou alteração administrativa é acessível sem JWT válido.
- Todos os controles visíveis do painel executam a ação correspondente ou exibem resposta clara.
- A agenda completa pode ser editada sem manipular JSON bruto ou IDs.
- Locais exigem somente um nome e podem representar qualquer tipo de espaço.
- Eixos são apresentados e armazenados com termos em português.
- `schedule.json` permanece consumível diretamente pelo frontend público.
- Escritas inválidas ou incompletas não corrompem os arquivos existentes.
- Testes de API e Playwright passam usando dados isolados.

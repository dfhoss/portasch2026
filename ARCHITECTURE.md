# Arquitetura do monólito

## 1. Objetivo e escopo

O projeto é um monólito FastAPI que reúne a API, a página pública e o painel
administrativo. A arquitetura separa composição da aplicação, contratos HTTP,
modelos de domínio, persistência e os dois domínios visuais.

## 2. Visão estrutural — nível 1

```mermaid
flowchart LR
    Browser[ navegador / site público ] --> Site[ static/site/ ]
    Browser --> PublicData[ GET /db/{file_name} ]
    Browser --> Admin[ static/admin/ ]
    Site --> App[ app.py ]
    PublicData --> App
    Admin --> App
    Client[ cliente HTTP ] --> App
    App --> Routes[ routes/ ]
    Routes --> Dependencies[ dependencies.py ]
    Routes --> Models[ models/ ]
    Routes --> Clients[ clients/ ]
    Clients --> JSON[ db/*.json ]
    App --> PublicDesign[ static/site/DESIGN.md ]
    App --> AdminDesign[ static/admin/DESIGN.md ]
```

### Catálogo de elementos

| Elemento          | Responsabilidade                                         | Interface principal                    |
| ----------------- | -------------------------------------------------------- | -------------------------------------- |
| `app.py`          | Compor a aplicação, lifespan, logging, saúde e routers   | HTTP / composição FastAPI              |
| `routes/`         | Validar requisições, autenticar e orquestrar respostas   | Endpoints FastAPI                      |
| `routes/site.py`  | Entregar somente os quatro JSONs públicos por allowlist | `GET /db/{file_name}`                  |
| `dependencies.py` | JWT, autorização, configuração e recursos compartilhados | `Depends` / aliases `Annotated`        |
| `models/`         | Contratos e validações de domínio reutilizáveis          | Pydantic                               |
| `clients/`        | Ler, validar e persistir dados; encapsular erros         | Dicionários, listas e erros de domínio |
| `clients/settings.py` | Caminho, leitura e persistência de `settings.json`   | `SETTINGS_PATH` / `SettingsDocument`   |
| `db/*.json`       | Catálogos de desenvolvimento persistidos                 | Arquivos JSON                          |
| `static/site/`    | Página pública, assets e scripts da agenda                | HTML, CSS e JavaScript                 |
| `static/admin/`   | Shell build-free do painel administrativo                | HTML, CSS e JavaScript                 |
| `static/site/DESIGN.md` | Tokens e contratos visuais da página pública        | Documento de design                    |
| `static/admin/DESIGN.md` | Tokens e contratos visuais do painel             | Documento de design                    |

As relações são direcionais: handlers usam clients e dependências; clients não devem
depender da camada HTTP. Não importe routers novos em `dependencies.py`, pois isso pode
criar ciclos de importação.

## 3. Visões de runtime

### 3.1 Requisição autenticada

```text
cliente -> app.py -> router -> CurrentTokenData/JWT
        -> modelo Pydantic -> client/repositório -> JSON atômico -> resposta HTTP
```

Handlers devem validar entrada, chamar a lógica da feature e moldar a resposta. Erros
de domínio são convertidos em `HTTPException` somente na fronteira HTTP.

### 3.2 Página pública

`/` entrega o shell público e seus assets build-free. Depois do carregamento, `schedule.js`
faz somente quatro requisições `GET /db/{file_name}` para `schedule.json`,
`knowledge_axes.json`, `locations.json` e `settings.json`. `routes/site.py` resolve cada
caminho em tempo de requisição, aplica allowlist e não participa da API administrativa. O
HTML inicial não contém agenda persistida; se a rede, o HTTP ou o parse falhar, a agenda e o
carrossel ficam vazios e o restante da página continua utilizável. Os tokens permanecem em
`static/site/DESIGN.md`.

### 3.3 Painel administrativo

```text
login -> /api/auth/token -> sessionStorage.adminToken
      -> /api/auth/users/me/ -> /api/* com Bearer JWT
      -> router -> client -> catálogo JSON
      -> /api/settings -> clients.settings -> settings.json
```

`/admin` entrega somente o shell público; o navegador valida a identidade antes de
buscar dados protegidos. O HTML inicial não deve conter agenda, catálogos, credenciais,
hashes ou IDs persistidos.

### 3.4 Falha em operação multi-arquivo

```text
validar estado atual -> gravar primeiro catálogo -> gravar segundo catálogo
                     -> sucesso
                     -> falha: restaurar o primeiro catálogo e relatar PersistenceError
```

Este fluxo é especialmente importante ao renomear um local, pois o nome também é
propagado para as sessões da agenda.

## 4. Conceitos e invariantes

### Persistência JSON

- Caminhos `DATABASE_PATH`, `SCHEDULE_PATH`, `SETTINGS_PATH`, `LOCATIONS_PATH` e
  `KNOWLEDGE_AXES_PATH` são resolvidos em tempo de chamada, nunca cacheados no import.
- Escritas usam arquivo temporário, `fsync` e `os.replace`; repositórios expõem falhas
  de filesystem como `PersistenceError`, não como detalhes HTTP.
- A agenda valida referências antes de salvar; `null` para local ou eixo é válido.
- `settings.json` mantém `eventDate` separado de `schedule.json`; `/api/settings` é a fronteira
  autenticada de leitura e gravação, enquanto `/db/settings.json` é somente leitura pública.
- Dados de usuários e hashes são sensíveis e nunca devem ser incluídos em código,
  HTML inicial ou fixtures versionadas.

### Catálogos e identidade

- Renomear eixo preserva o ID e não reescreve referências da agenda.
- Local ou eixo referenciado não pode ser excluído; o conflito deve informar as atividades
  afetadas.
- Nomes são normalizados por Unicode, espaços e caixa antes da comparação.
- IDs persistidos não devem ser derivados da posição dos itens na lista.
- O catálogo de locais mantém grupos tipados e salas relacionadas por `groupId`; a agenda
  referencia os nomes das salas e cada sessão pode conter uma lista `locations`.

### Camadas e contratos

- Use Pydantic para modelos de entrada e resposta pública; evite dicionários não tipados
  como contrato.
- Clients retornam valores de domínio ou `None` e lançam exceções específicas; não devem
  conhecer status codes ou `HTTPException`.
- Utilities devem ser independentes do framework e reutilizáveis entre features.
- Preserve endpoints assíncronos quando apropriado, mas não trate I/O síncrono de arquivo
  como assíncrono sem introduzir um client de armazenamento assíncrono.

## 5. Deployment e configuração

O ambiente local executa a aplicação com Uvicorn. A API é servida em `/api`, com
documentação em `/api/docs`; a página pública é servida em `/`; o painel é servido
em `/admin`, com assets em `/admin/static`. Os catálogos JSON são substituíveis
por caminhos de ambiente para testes e deployments isolados.

No Docker Compose, a pasta `./db` do workspace é montada diretamente em `/app/db`.
Assim, os catálogos usados pela API e pelos JSONs públicos permanecem disponíveis
quando a imagem é recriada e as alterações feitas pelo painel ficam no workspace;
não há volume nomeado separado para essa persistência.

O `TOKEN_JWT` já está configurado em `.env`. O segredo deve permanecer fora do Git e o
lifespan deve validar apenas configurações exigidas pela aplicação inteira.

## 6. Padrão para adicionar uma feature

1. Identifique o contrato e as invariantes; crie ou atualize modelos em `models/` quando
   forem compartilhados.
2. Encapsule leitura, escrita, caminhos e erros de armazenamento em `clients/`.
3. Crie um router com prefixo, tags, modelos Pydantic, dependências e handlers finos.
4. Registre o router em `app.py`, sem mover regras de negócio para a composição global.
5. Adicione testes de sucesso, entrada inválida, ausência, autorização e consistência;
   use `TestClient`, JSON temporário e variáveis de ambiente isoladas.
6. Execute `uv run ruff check .`, `uv run ruff format --check .`, `uv run ty check` e
   `uv run pytest`. Para E2E, instale Chromium previamente com Playwright.
7. Atualize esta documentação se a mudança alterar uma fronteira, fluxo, invariável,
   decisão ou padrão de feature.

## 7. Quando introduzir `services/`

Adicione `services/<feature>.py` entre router e client somente quando regras de negócio
forem reutilizadas ou deixarem de caber claramente no handler. Não crie a camada apenas
para repassar chamadas.

## 8. Decisões arquiteturais e evolução

Para uma decisão que altere fronteiras, persistência, segurança, integração ou qualidade
do sistema, registre um ADR separado contendo:

- contexto e problema;
- opções consideradas;
- decisão escolhida e justificativa;
- consequências, riscos e plano de revisão.

Ligue o ADR a esta arquitetura e remova ou marque como obsoleta qualquer descrição que
deixe de refletir o código. A documentação deve explicar o “porquê” das decisões, não
duplicar cada detalhe de implementação.

## 9. Referências para manutenção da arquitetura

- [Awesome ARCHITECTURE.md](https://github.com/noahbald/awesome-architecture-md) — exemplos
  de mapas de código, diagramas, invariantes e decisões de design.
- [Architecture View Template](https://github.com/pmerson/architecture-view-template) —
  modelo de visão estrutural, catálogo de elementos, comportamento e ADRs relacionados.
- [arc42 — Building Block View](https://docs.arc42.org/section-5/) — decomposição hierárquica
  em building blocks e responsabilidades.
- [C4 Model](https://c4model.com/) — níveis de contexto, containers, componentes e código.
- [MADR](https://adr.github.io/madr/) — formato para registrar decisões arquiteturais,
  justificativas e consequências.

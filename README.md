# Portas Abertas UFFS

Monólito FastAPI que reúne a API, a página pública e o painel administrativo do evento.

## Configuração e execução

Instale o `uv` e o Python necessário:

```powershell
winget install --id astral-sh.uv -e
uv python install 3.14
uv sync
Copy-Item .env.example .env
```

Defina um valor seguro para `TOKEN_JWT` em `.env`. A aplicação carrega esse arquivo
automaticamente ao iniciar; variáveis já definidas no ambiente têm prioridade:

```powershell
uv run uvicorn app:app --reload
```

A opção `[tool.uv] compile-bytecode = false` em `pyproject.toml` impede que o `uv`
pré-compile dependências durante a sincronização. Ela não controla o cache que o
interpretador Python pode criar ao importar módulos durante a execução local.

## Deploy com Docker

O `Dockerfile` usa build multi-stage com Python 3.14 e instala somente as
dependências de produção a partir do `uv.lock`. O `docker-compose.yml` publica o
backend e as interfaces estáticas pelo mesmo serviço e mantém os catálogos JSON
da pasta `db/` do workspace montados em `/app/db`. A imagem não inclui arquivos da
pasta `db/`; os dados são fornecidos pelo volume do Compose. O contexto de build
contém somente manifests, código e assets usados em runtime.

Copie o arquivo de ambiente, defina um segredo seguro e inicie o serviço:

```powershell
Copy-Item .env.example .env
docker compose up -d --build
```

O serviço fica disponível em <http://localhost:8000>. Para acompanhar os logs:

```powershell
docker compose logs -f app
```

As alterações feitas no painel são armazenadas diretamente nos arquivos da pasta
`db/` do workspace. Para remover o container sem apagar os dados, use:

```powershell
docker compose down
```

Endereços locais:

- API: <http://localhost:8000/api/docs>
- Site público: <http://localhost:8000/>
- Painel administrativo: <http://localhost:8000/admin>

O painel exige login e mantém o token somente no `sessionStorage`. As alterações são
validadas pela API e persistidas nos arquivos JSON configurados.

O site público lê, somente por `GET`, `schedule.json`, `knowledge_axes.json`, `locations.json`
e `settings.json` em `/db/{file_name}`. Ele não usa `/api/` nem possui permissão de escrita.
`eventDate` é mantido exclusivamente em `settings.json`; para fornecer um valor específico em
um ambiente isolado, crie um arquivo que contenha somente `{"eventDate":"2026-09-22"}` e execute:

```powershell
$env:SETTINGS_PATH = "C:\caminho\settings-simulacao.json"
uv run uvicorn app:app --reload
```

A agenda continua no caminho definido por `SCHEDULE_PATH`; a simulação não copia nem altera
`schedule.json`. A programação pública é exibida independentemente da data atual; os rótulos
`AO VIVO`, `EM BREVE` e `FINALIZADA` são calculados apenas pela hora atual nas sessões.

## Estrutura

| Caminho | Responsabilidade |
| --- | --- |
| `app.py` | Composição da aplicação FastAPI |
| `routes/` | Endpoints HTTP e entrega das interfaces |
| `models/` | Contratos Pydantic e validações |
| `clients/` | Persistência e regras de acesso aos JSONs |
| `db/` | Dados persistidos da aplicação |
| `static/site/` | Página pública, CSS, JavaScript e assets |
| `static/admin/` | Painel administrativo build-free |
| `static/site/DESIGN.md` | Tokens e contratos visuais do site |
| `static/admin/DESIGN.md` | Tokens e contratos visuais do painel |
| `tests/` | Testes da API, painel e site |
| `ARCHITECTURE.md` | Arquitetura geral do monólito |

O [ARCHITECTURE.md](ARCHITECTURE.md) descreve as fronteiras do sistema. Cada interface
possui seu próprio contrato visual junto aos arquivos que ela governa.

## Site público

O site é estático e não possui `package.json`, bundler ou dependências próprias. Seus
arquivos principais são `static/site/index.html`, `static/site/css/`,
`static/site/js/` e `static/site/assets/`. O HTML inicial contém apenas o shell da agenda e
do carrossel; `schedule.js` consulta os quatro JSONs públicos em `/db/` e renderiza os dados
reais sem usar a API administrativa. Se a rede falhar, o shell, o hero, o regulamento e os
mapas continuam utilizáveis e a programação permanece vazia.

As fontes locais usam `font-display: swap`. O hero usa as artes desktop e mobile via
`picture`, com breakpoint móvel em 600px. O carrossel é responsivo, circular, suporta
teclado e swipe, e respeita `prefers-reduced-motion`.
Os quatro mapas do campus usam `loading="lazy"` para carregar quando se aproximam da tela,
liberando a rede inicial para a agenda e o carrossel.
Os quatro JSONs públicos da agenda usam `preload` no `<head>`, antes da execução de `schedule.js`,
para que os dados comecem a baixar junto com os recursos do shell.

Para decisões de interface, consulte [`static/site/DESIGN.md`](static/site/DESIGN.md).

## Testes e qualidade

Instale o navegador usado pela suíte E2E quando necessário:

```powershell
uv run playwright install chromium
```

Comandos úteis:

```powershell
uv run pytest -v
uv run pytest tests/e2e/test_home_panel.py -v
uv run pytest tests/site -v
uv run ruff check .
uv run ruff format --check .
uv run ty check
```

Os testes E2E usam diretórios temporários e podem receber caminhos isolados por
`DATABASE_PATH`, `SCHEDULE_PATH`, `SETTINGS_PATH`, `LOCATIONS_PATH` e
`KNOWLEDGE_AXES_PATH`. O
`TOKEN_JWT` também deve estar configurado.

## Desenvolvimento visual

Antes de alterar o painel, leia [`static/admin/DESIGN.md`](static/admin/DESIGN.md).
Antes de alterar o site público, leia [`static/site/DESIGN.md`](static/site/DESIGN.md).
Novos tokens, regras de acessibilidade, foco, responsividade ou animações reduzidas
devem ser documentados no contrato visual correspondente.

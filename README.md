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

Defina um valor seguro para `TOKEN_JWT` em `.env` e inicie o servidor:

```powershell
uv run uvicorn app:app --reload --env-file .env
```

Endereços locais:

- API: <http://localhost:8000/api/docs>
- Site público: <http://localhost:8000/site/>
- Painel administrativo: <http://localhost:8000/home>

O painel exige login e mantém o token somente no `sessionStorage`. As alterações são
validadas pela API e persistidas nos arquivos JSON configurados.

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
`static/site/js/` e `static/site/assets/`. A agenda, os eixos e os locais continuam
tendo os JSONs do diretório `db/` como fonte de verdade; não replique dados de negócio
nos scripts JavaScript.

As fontes locais usam `font-display: swap`. O hero usa as artes desktop e mobile via
`picture`, com breakpoint móvel em 600px. O carrossel é responsivo, circular, suporta
teclado e swipe, e respeita `prefers-reduced-motion`.

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
`DATABASE_PATH`, `SCHEDULE_PATH`, `LOCATIONS_PATH` e `KNOWLEDGE_AXES_PATH`. O
`TOKEN_JWT` também deve estar configurado.

## Desenvolvimento visual

Antes de alterar o painel, leia [`static/admin/DESIGN.md`](static/admin/DESIGN.md).
Antes de alterar o site público, leia [`static/site/DESIGN.md`](static/site/DESIGN.md).
Novos tokens, regras de acessibilidade, foco, responsividade ou animações reduzidas
devem ser documentados no contrato visual correspondente.

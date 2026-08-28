# Portas Abertas API

Backend FastAPI minimalista gerenciado com `uv`.

## Configuração

Instale o `uv` no Windows:

```powershell
winget install --id astral-sh.uv -e
```

Instale a versão necessária do Python por meio do `uv`:

```powershell
uv python install 3.14
```

A partir da raiz do repositório, entre no diretório do backend e instale as dependências fixadas no arquivo de lock:

```powershell
cd backend
uv sync
Copy-Item .env.example .env
```

Defina um valor seguro para `TOKEN_JWT` no arquivo `.env` e inicie o servidor de desenvolvimento:

```powershell
uv run uvicorn app:app --reload --env-file .env
```

Acesse `http://localhost:8000/api/docs` para consultar a documentação interativa da API.

## Painel administrativo

Com o servidor em execução, abra `http://localhost:8000/admin`. O painel exige login e mantém o
token somente no `sessionStorage` do navegador. As alterações da programação, locais e eixos são
validadas pela API e persistidas nos arquivos JSON configurados.

Para instalar o navegador usado pela suíte E2E (a instalação não é feita automaticamente pelos
testes):

```powershell
uv run playwright install chromium
```

Comandos úteis, executados dentro de `backend`:

```powershell
uv run pytest -v
uv run pytest tests/e2e/test_admin_panel.py -v
uv run ruff check .
uv run ruff format --check .
uv run ty check
```

Os testes E2E iniciam um Uvicorn local em porta efêmera e copiam `users.json`, `schedule.json`,
`locations.json` e `knowledge_axes.json` para diretórios temporários isolados. Para alterar os
caminhos em uma execução manual, defina `DATABASE_PATH`, `SCHEDULE_PATH`, `LOCATIONS_PATH` e
`KNOWLEDGE_AXES_PATH`; `TOKEN_JWT` também deve estar configurado.

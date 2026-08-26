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

import sys
from contextlib import asynccontextmanager

import uvicorn
from clients.db import load_database
from dependencies import validate_jwt_configured
from fastapi import FastAPI, status
from fastapi.responses import RedirectResponse
from loguru import logger
from routes import auth
from utils import brazil_time_formatter, get_brazil_time

logger.configure(
    handlers=[
        {
            "sink": sys.stderr,
            "level": "DEBUG",
            "format": "[{level}] {time} | {message}\n{exception}",
        }
    ]
)
logger = logger.patch(lambda record: record.update(time=brazil_time_formatter(record)))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await validate_jwt_configured()
    load_database()
    yield


# Tags metadata for better API documentation
tags_metadata = [
    {
        "name": "auth",
        "description": "Autenticação e autorização - endpoints para login, registro e gerenciamento de usuários",
    },
    {
        "name": "Health",
        "description": "Verificação de saúde e status do sistema",
    },
]

app = FastAPI(
    title="Orchestrator do Backend de IA GeoGIS",
    description="Orchestrator FastAPI para gerenciar tarefas de OCR Bedrock através de filas SQS",
    version="1.0.0",
    docs_url="/docs",  # Explicitly enable docs
    redoc_url="/redoc",  # Enable ReDoc as well
    openapi_url="/openapi.json",  # Ensure OpenAPI spec is available
    root_path="/api",  # This tells FastAPI about the API Gateway stage prefix
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)
app.include_router(auth.router)


@app.get("/", tags=["Root"])
async def read_root():
    """
    **Endpoint raiz - Redirecionamento para documentação**

    Redireciona automaticamente para a documentação interativa da API.
    Este endpoint serve como ponto de entrada conveniente para acessar a documentação completa da API.

    **Redireciona para:** `/docs`

    **Casos de Uso:**
    - Acesso rápido à documentação da API
    - Ponto de entrada padrão para desenvolvedores
    """
    return RedirectResponse(url="/api/docs", status_code=status.HTTP_302_FOUND)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    **Endpoint de verificação de saúde do sistema**

    Fornece status de saúde em tempo real e informações do sistema para fins de monitoramento e alerta.
    Retorna metadados do serviço incluindo timestamp atual e identificação do serviço.

    **Retorna:**
    - **status** (string): Status de saúde atual ("healthy" | "degraded" | "unhealthy")
    - **timestamp** (string): Timestamp formatado em ISO no fuso horário do Brasil
    - **service** (string): Nome e identificador do serviço

    **Casos de Uso:**
    - Verificações de saúde do load balancer
    - Integração com sistema de monitoramento
    - Descoberta de serviço e verificação de status
    - Alerta automatizado e resposta a incidentes
    """
    return {
        "status": "healthy",
        "timestamp": get_brazil_time(),
        "service": "GeoGIS AI Backend Orchestrator",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)

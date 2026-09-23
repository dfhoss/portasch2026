# ruff: noqa: E402

import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from loguru import logger

load_dotenv(Path(__file__).resolve().with_name(".env"), override=False)

from clients.db import load_database
from dependencies import validate_jwt_configured
from routes import (
    auth,
    home,
    institutions,
    knowledge_axes,
    locations,
    participants,
    schedule,
    settings,
    site,
)
from utils import brazil_time_formatter, get_brazil_time

logger.configure(
    handlers=[
        {
            "sink": sys.stderr,
            "level": "DEBUG",
            "format": brazil_time_formatter,
        }
    ]
)


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
    title="Portas Abertas API",
    description=(
        "API do evento Portas Abertas para gerenciamento da programação, "
        "locais, eixos de conhecimento e painel administrativo."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)
API_PREFIX = "/api"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(schedule.router, prefix=API_PREFIX)
app.include_router(settings.router, prefix=API_PREFIX)
app.include_router(locations.router, prefix=API_PREFIX)
app.include_router(knowledge_axes.router, prefix=API_PREFIX)
app.include_router(institutions.router, prefix=API_PREFIX)
app.include_router(participants.router, prefix=API_PREFIX)
app.include_router(site.router)
app.mount(
    "/admin/static",
    home.AdminStaticFiles(directory=home.ADMIN_STATIC_DIR),
    name="admin-static",
)
app.include_router(home.router)


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
        "service": "Portas Abertas API",
    }


app.mount(
    "/",
    site.PublicSiteStaticFiles(directory=site.SITE_STATIC_DIR, html=True),
    name="public-site",
)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)

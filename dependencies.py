"""
Centralizado de dependências reutilizáveis para todas as rotas FastAPI.

Este módulo fornece dependências que podem ser reutilizadas em múltiplos endpoints,
seguindo o padrão Annotated do FastAPI (versão 0.95.0+).

Dependências incluem:
- Autenticação e autorização de usuários
- Validação da configuração do JWT
- Acesso ao armazenamento local de usuários em JSON
"""

import os
from typing import Annotated

from clients.db import DATABASE_PATH, database_connection, load_database
from fastapi import Depends, HTTPException, status
from loguru import logger
from routes.auth import TokenData, get_token_data

# Environment variables
TOKEN_JWT = os.environ.get("TOKEN_JWT")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440


# ============================================================================
# DEPENDENCIES - Configurações e Validações
# ============================================================================


async def validate_jwt_configured() -> tuple[str, str]:
    """
    Dependency: Valida se o JWT está configurado.

    Raises:
        HTTPException: Se TOKEN_JWT não estiver configurado

    Returns:
        tuple[str, str]: (JWT secret, Algorithm)

    Usage:
        jwt_config: Annotated[tuple[str, str], Depends(validate_jwt_configured)]
    """
    if not TOKEN_JWT:
        logger.error("TOKEN_JWT não configurado")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "TOKEN_JWT não configurado"},
        )
    return (TOKEN_JWT, ALGORITHM)


async def validate_database_configured() -> str:
    """
    Dependency: Valida se o DATABASE_PATH está configurada.

    Raises:
        HTTPException: Se DATABASE_PATH não estiver configurada

    Returns:
        str: DATABASE_PATH

    Usage:
        db_url: Annotated[str, Depends(validate_database_configured)]
    """
    if not DATABASE_PATH:
        logger.error("DATABASE_PATH não configurada")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "DATABASE_PATH não configurada"},
        )
    return DATABASE_PATH


async def get_db_service():
    """
    Dependency: Retorna os dados do banco local de usuários.

    Yields:
        dict: Conteúdo do arquivo JSON de usuários

    Usage:
        db_data: Annotated[dict, Depends(get_db_service)]
    """
    with database_connection(DATABASE_PATH) as db_service:
        yield db_service


def get_db_client():
    """
    Dependency: Retorna os dados carregados do banco local de usuários.

    Raises:
        HTTPException: Se DATABASE_PATH não estiver configurada

    Returns:
        dict: Conteúdo do arquivo JSON de usuários

    Usage:
        db_data: Annotated[dict, Depends(get_db_client)]
    """
    return load_database(DATABASE_PATH)


# ============================================================================
# COMPOSITE DEPENDENCIES - Tipos alias para uso em endpoints
# ============================================================================


# Token de autenticação validado
CurrentTokenData = Annotated[TokenData, Depends(get_token_data)]

# JWT configurado (secret, algorithm)
JWTConfig = Annotated[tuple[str, str], Depends(validate_jwt_configured)]

# Database URL configurada
DatabaseURL = Annotated[str, Depends(validate_database_configured)]

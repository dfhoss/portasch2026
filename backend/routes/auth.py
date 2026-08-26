import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
import jwt
from clients.db import get_user as get_user_from_db
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import (
    HTTPBearer,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from loguru import logger
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

security = HTTPBearer()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    id: int
    user_type: str
    username: str


class UserInDB(User):
    hashed_password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_pw_bytes = (
        plain_password.encode("utf-8") if isinstance(plain_password, str) else plain_password
    )
    hashed_pw_bytes = (
        hashed_password.encode("utf-8") if isinstance(hashed_password, str) else hashed_password
    )
    result = bcrypt.checkpw(plain_pw_bytes, hashed_pw_bytes)
    return result


def get_password_hash(password: str) -> str:
    pw_bytes = password.encode("utf-8") if isinstance(password, str) else password
    hashed = bcrypt.hashpw(pw_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def get_user(username: str):
    """Retrieve a user by its username."""
    try:
        user = get_user_from_db(username)
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        return None

    return UserInDB(**user) if user else None


def authenticate_user(username: str, password: str, session=None):
    """Authenticate a user using optional SQLAlchemy session.

    When called from a route, pass the injected RDS session to reuse the
    connection (same pattern used in other routers).
    """
    user = get_user(username=username)
    if not user:
        return False
    if not verify_password(plain_password=password, hashed_password=user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create a JWT using the TOKEN_JWT secret from the environment.

    We intentionally resolve the secret at call time to avoid import-time
    dependency on `dependencies.py` (which imports this module).
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})

    secret = os.environ.get("TOKEN_JWT")
    if not secret:
        logger.error("TOKEN_JWT environment variable is not set")
        raise RuntimeError("TOKEN_JWT environment variable is not set")

    encoded_jwt = jwt.encode(to_encode, secret, algorithm=ALGORITHM)
    return encoded_jwt


async def get_token_data(token: Annotated[str, Depends(oauth2_scheme)]):
    """Validate JWT token and return token data without querying the database.

    The token is validated by checking its signature and expiration time.
    If the token is valid, user information is extracted from the token payload.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        secret = os.environ.get("TOKEN_JWT")
        if not secret:
            logger.error("TOKEN_JWT environment variable is not set")
            raise credentials_exception

        # jwt.decode() validates the token signature and expiration automatically
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            logger.error("JWT missing 'sub' claim: %s", payload)
            raise credentials_exception

        # Return token data without database lookup
        return TokenData(username=username)
    except jwt.ExpiredSignatureError:
        logger.error("JWT token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid JWT token: {e}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Unexpected error decoding JWT: {e}")
        raise credentials_exception


@router.get("/users/me/", response_model=TokenData)
async def read_users_me(
    token_data: Annotated[TokenData, Depends(get_token_data)],
):
    """Get current user information from the JWT token."""
    return token_data


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

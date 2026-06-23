from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Response, status
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from passlib.context import CryptContext

from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash bcrypt fixo (não computado em runtime). Usado quando o email não existe
# para que verify_password rode mesmo assim e proteja contra enumeração de
# emails via timing attack.
DUMMY_HASH = "$2b$12$KIXqq3yQ1OQ9Hg5cN1.lZuV4w6sTl9JzL7JzVlYxR4sV9N0wRzv5G"


# Tipos canônicos de token. O claim "type" no JWT distingue access de refresh
# e impede que um stolen refresh seja usado como access (e vice-versa).
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _encode(sub: str, token_type: str, expires_delta: timedelta) -> str:
    payload = {
        "sub": sub,
        "type": token_type,
        "exp": datetime.now(UTC) + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(sub: str, expires_delta: timedelta | None = None) -> str:
    return _encode(
        sub,
        TOKEN_TYPE_ACCESS,
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(sub: str, expires_delta: timedelta | None = None) -> str:
    return _encode(
        sub,
        TOKEN_TYPE_REFRESH,
        expires_delta or timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str, expected_type: str) -> dict:
    """Valida assinatura, expiração e tipo. Levanta 401 com detail apropriado."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão expirada",
        ) from exc
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        ) from exc

    if payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

    return payload


def set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    response.set_cookie(
        key=settings.cookie_name,
        value=access,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    for name in (settings.cookie_name, settings.refresh_cookie_name):
        response.delete_cookie(
            key=name,
            path="/",
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
        )

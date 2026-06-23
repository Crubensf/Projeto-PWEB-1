from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from config import settings
from db import get_db
from models import Usuario
from security import TOKEN_TYPE_ACCESS, decode_token


def get_usuario_from_token(
    request: Request,
    db: Session = Depends(get_db),
) -> Usuario:
    token = request.cookies.get(settings.cookie_name)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado",
        )

    payload = decode_token(token, expected_type=TOKEN_TYPE_ACCESS)

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

    user = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
        )

    return user


def require_perfil(perfil: str):
    def _dep(user: Usuario = Depends(get_usuario_from_token)) -> Usuario:
        if user.perfil != perfil:
            raise HTTPException(status_code=403, detail=f"Apenas {perfil}s")
        return user

    return _dep


get_motorista = require_perfil("motorista")
get_estudante = require_perfil("estudante")

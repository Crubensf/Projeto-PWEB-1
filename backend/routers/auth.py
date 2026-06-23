from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from pydantic import EmailStr
from sqlalchemy.orm import Session

import auditoria
from config import settings
from db import get_db
from models import Usuario
from rate_limit import (
    checar_rate_limit_login,
    checar_rate_limit_registro,
    get_client_ip,
    limpar_falhas_login,
    registrar_falha_login,
)
from schemas import LoginData, Token, UsuarioOut
from security import (
    DUMMY_HASH,
    TOKEN_TYPE_REFRESH,
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    set_auth_cookies,
    verify_password,
)
from validation import validar_cnh, validar_perfil, validar_senha

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _emitir_tokens(response: Response, user: Usuario) -> None:
    access = create_access_token(sub=str(user.id))
    refresh = create_refresh_token(sub=str(user.id))
    set_auth_cookies(response, access, refresh)


@router.post("/register", response_model=Token)
async def registrar_usuario(
    request: Request,
    response: Response,
    nome: str = Form(...),
    email: EmailStr = Form(...),
    senha: str = Form(...),
    perfil: str = Form(...),
    cnh: str | None = Form(None),
    db: Session = Depends(get_db),
):
    checar_rate_limit_registro(get_client_ip(request))
    validar_perfil(perfil)
    validar_senha(senha)
    if perfil == "motorista":
        validar_cnh(cnh)

    if db.query(Usuario).filter(Usuario.email == email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    user = Usuario(
        nome=nome.strip(),
        email=email,
        senha_hash=hash_password(senha),
        perfil=perfil,
        cnh=cnh if perfil == "motorista" else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    auditoria.log_evento(
        db,
        auditoria.REGISTRO,
        usuario_id=user.id,
        ip=get_client_ip(request),
        detalhe=f"perfil={perfil}",
    )

    _emitir_tokens(response, user)
    return Token(usuario=UsuarioOut.model_validate(user))


@router.post("/login", response_model=Token)
def login(
    data: LoginData,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    email_norm = (data.email or "").lower().strip()
    checar_rate_limit_login(email_norm)

    user = db.query(Usuario).filter(Usuario.email == email_norm).first()

    if user:
        senha_valida = verify_password(data.senha, user.senha_hash)
    else:
        verify_password(data.senha, DUMMY_HASH)
        senha_valida = False

    ip = get_client_ip(request)
    if not user or not senha_valida:
        registrar_falha_login(email_norm)
        auditoria.log_evento(db, auditoria.LOGIN_FALHA, ip=ip, detalhe=f"email={email_norm}")
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    limpar_falhas_login(email_norm)
    auditoria.log_evento(db, auditoria.LOGIN_SUCESSO, usuario_id=user.id, ip=ip)
    _emitir_tokens(response, user)
    return Token(usuario=UsuarioOut.model_validate(user))


@router.post("/refresh", response_model=Token)
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Troca refresh cookie por novo par (access + refresh). Rotação completa."""
    token = request.cookies.get(settings.refresh_cookie_name)
    if not token:
        raise HTTPException(status_code=401, detail="Refresh ausente")

    payload = decode_token(token, expected_type=TOKEN_TYPE_REFRESH)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Refresh inválido")

    user = db.query(Usuario).filter(Usuario.id == int(sub)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    _emitir_tokens(response, user)
    return Token(usuario=UsuarioOut.model_validate(user))


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    # Identifica usuário pelo access cookie (mesmo expirado, claim sub é legível)
    usuario_id: int | None = None
    token = request.cookies.get(settings.cookie_name)
    if token:
        try:
            from jose import jwt

            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm],
                options={"verify_exp": False},
            )
            sub = payload.get("sub")
            if sub:
                usuario_id = int(sub)
        except Exception:
            pass

    auditoria.log_evento(db, auditoria.LOGOUT, usuario_id=usuario_id, ip=get_client_ip(request))
    clear_auth_cookies(response)
    return {"message": "Logout realizado com sucesso"}

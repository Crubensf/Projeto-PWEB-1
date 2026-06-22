import os
from datetime import datetime, timedelta, date, timezone
from typing import Optional, List

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
    Form,
    Query,
    Response,
    Request,
)
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from pydantic import EmailStr

from db import get_db
from models import Usuario, Rota, Viagem
from schemas import (
    UsuarioOut,
    UsuarioCreate,
    UsuarioUpdate,
    LoginData,
    Token,
    RotaCreate,
    RotaUpdate,
    RotaOut,
    ViagemCreate,
    ViagemUpdate,
    ViagemOut,
    MotoristaResumo,
)


# CONFIG GERAL / AUTH


# Lê da variável de ambiente; fallback só para desenvolvimento local
SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key_nao_usar_em_producao")
ALGORITHM = "HS256"

# Cookie de autenticação — atributos centralizados
COOKIE_NAME = "access_token"
COOKIE_MAX_AGE = 60 * 60 * 8  # 8h, casa com a expiração do JWT
COOKIE_SECURE = True  # HTTPS ativo via Apache
COOKIE_SAMESITE = "lax"


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=COOKIE_MAX_AGE,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    # Para o browser remover o cookie, os atributos precisam casar com os do set
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="Van Já API")

# Aceita qualquer origem em HTTP vindas de localhost, 127.0.0.1 ou redes privadas
# (192.168.x.x, 10.x.x.x, 172.16-31.x.x) em qualquer porta — necessário para acesso via LAN
# Em produção o frontend é servido pelo Apache no mesmo domínio,
# portanto as chamadas /api/ não são cross-origin e o CORS não é ativado.
# Mantemos a regra abaixo para dev local (sem Docker).
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=(
        r"https?://(localhost|127\.0\.0\.1"
        r"|192\.168\.\d{1,3}\.\d{1,3}"
        r"|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        r"|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})"
        r"(:\d+)?"
    ),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
    max_age=3600,
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    # Defesa contra MIME sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Clickjacking: API não deve ser embutida em frames
    response.headers["X-Frame-Options"] = "DENY"
    # Não vaza URL completa em referer para sites externos
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Desabilita APIs sensíveis do browser que a API não precisa
    response.headers["Permissions-Policy"] = (
        "geolocation=(), camera=(), microphone=(), payment=()"
    )
    return response



# HELPERS GERAIS


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# Hash bcrypt fixo (não computado em runtime, evita disparar detecção do passlib
# no import). Usado quando o email não existe para que `verify_password` rode
# mesmo assim e proteja contra enumeração de emails via timing attack.
_DUMMY_HASH = "$2b$12$KIXqq3yQ1OQ9Hg5cN1.lZuV4w6sTl9JzL7JzVlYxR4sV9N0wRzv5G"


# ----- Validações de input -----

PERFIS_VALIDOS = ("estudante", "motorista")
MIN_SENHA = 6


def validar_senha(senha: str) -> None:
    if not senha or len(senha) < MIN_SENHA:
        raise HTTPException(
            status_code=400,
            detail=f"A senha deve ter no mínimo {MIN_SENHA} caracteres.",
        )


def validar_perfil(perfil: str) -> None:
    if perfil not in PERFIS_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"Perfil inválido. Use um de: {', '.join(PERFIS_VALIDOS)}.",
        )


def validar_cnh(cnh: Optional[str]) -> None:
    if not cnh or not cnh.isdigit() or len(cnh) != 11:
        raise HTTPException(
            status_code=400,
            detail="CNH deve ter exatamente 11 dígitos numéricos.",
        )


# ----- Rate limiting de login (in-memory, single instance) -----

MAX_TENTATIVAS = 5
JANELA_TENTATIVAS_S = 15 * 60  # 15 min

_tentativas_falhas: dict[str, list[datetime]] = {}


def _limpar_tentativas_expiradas(email: str) -> list[datetime]:
    agora = datetime.now(timezone.utc)
    atuais = _tentativas_falhas.get(email, [])
    atuais = [t for t in atuais if (agora - t).total_seconds() < JANELA_TENTATIVAS_S]
    _tentativas_falhas[email] = atuais
    return atuais


def checar_rate_limit_login(email: str) -> None:
    atuais = _limpar_tentativas_expiradas(email)
    if len(atuais) >= MAX_TENTATIVAS:
        raise HTTPException(
            status_code=429,
            detail="Muitas tentativas de login. Aguarde alguns minutos e tente novamente.",
        )


def registrar_falha_login(email: str) -> None:
    _tentativas_falhas.setdefault(email, []).append(datetime.now(timezone.utc))


def limpar_falhas_login(email: str) -> None:
    _tentativas_falhas.pop(email, None)


# ----- Rate limiting de cadastro por IP (anti-spam) -----

MAX_REGISTROS_POR_IP = 5
JANELA_REGISTRO_S = 60 * 60  # 1h

_registros_por_ip: dict[str, list[datetime]] = {}


def checar_rate_limit_registro(ip: str) -> None:
    agora = datetime.now(timezone.utc)
    atuais = _registros_por_ip.get(ip, [])
    atuais = [t for t in atuais if (agora - t).total_seconds() < JANELA_REGISTRO_S]
    _registros_por_ip[ip] = atuais
    if len(atuais) >= MAX_REGISTROS_POR_IP:
        raise HTTPException(
            status_code=429,
            detail="Muitos cadastros recentes desse endereço. Tente novamente mais tarde.",
        )
    atuais.append(agora)


def get_client_ip(request: Request) -> str:
    # Confia em X-Forwarded-For atrás de proxy reverso; senão usa o socket direto
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def create_access_token(sub: str, expires_delta: Optional[timedelta] = None):
    to_encode = {"sub": sub}
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=8))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def salvar(db: Session, obj):
    
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_usuario_from_token(
    request: Request,
    db: Session = Depends(get_db),
):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado",
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        # Token expirou — frontend pode capturar este detail e redirecionar pro login
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão expirada",
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

    user_id: Optional[str] = payload.get("sub")
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
    
    def _dep(user=Depends(get_usuario_from_token)):
        if user.perfil != perfil:
            raise HTTPException(status_code=403, detail=f"Apenas {perfil}s")
        return user
    return _dep


get_motorista = require_perfil("motorista")
get_estudante = require_perfil("estudante")



# HELPERS DE CONVERSÃO


def rota_to_out(r: Rota) -> RotaOut:
    return RotaOut(
        id=r.id,
        motorista_id=r.motorista_id,
        nome=r.nome,
        origem=r.origem,
        destino=r.destino,
        hora_ida=r.hora_ida,
        hora_volta=r.hora_volta,
        vagas=r.vagas,
        veiculo=r.veiculo,
        dias_semana=r.dias_semana.split(","),
        preco=r.preco,
    )


def viagem_to_out(v: Viagem) -> ViagemOut:
    rota_out = rota_to_out(v.rota)
    return ViagemOut(
        id=v.id,
        rota=rota_out,
        data=v.data,
        status=v.status,
    )


# =========================
# ROTAS AUTH (LOGIN / CADASTRO)
# =========================

@app.post("/api/auth/register", response_model=Token)
async def registrar_usuario(
    request: Request,
    response: Response,
    nome: str = Form(...),
    email: EmailStr = Form(...),
    senha: str = Form(...),
    perfil: str = Form(...),
    cnh: Optional[str] = Form(None),
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

    user = salvar(db, user)

    token = create_access_token(sub=str(user.id))
    set_auth_cookie(response, token)

    return Token(usuario=UsuarioOut.model_validate(user))


@app.post("/api/auth/login", response_model=Token)
def login(
    data: LoginData,
    response: Response,
    db: Session = Depends(get_db),
):
    email_norm = (data.email or "").lower().strip()

    checar_rate_limit_login(email_norm)

    user = db.query(Usuario).filter(Usuario.email == email_norm).first()

    # Sempre roda bcrypt, mesmo se o usuário não existir, para que o tempo
    # de resposta não denuncie quais emails estão cadastrados (timing attack).
    if user:
        senha_valida = verify_password(data.senha, user.senha_hash)
    else:
        verify_password(data.senha, _DUMMY_HASH)
        senha_valida = False

    if not user or not senha_valida:
        registrar_falha_login(email_norm)
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    limpar_falhas_login(email_norm)

    token = create_access_token(sub=str(user.id))
    set_auth_cookie(response, token)

    return Token(usuario=UsuarioOut.model_validate(user))


@app.post("/api/auth/logout")
def logout(response: Response):
    clear_auth_cookie(response)
    return {"message": "Logout realizado com sucesso"}



# ROTAS USUÁRIO (CRUD)


@app.get("/api/usuarios/me", response_model=UsuarioOut)
def me(user=Depends(get_usuario_from_token)):
    return UsuarioOut.model_validate(user)


@app.put("/api/usuarios/me", response_model=UsuarioOut)
def atualizar_me(
    dados: UsuarioUpdate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_usuario_from_token),
):
    if dados.email and dados.email != user.email:
        if db.query(Usuario).filter(Usuario.email == dados.email).first():
            raise HTTPException(status_code=400, detail="E-mail já está em uso por outro usuário")

    if dados.nome is not None:
        user.nome = dados.nome
    if dados.email is not None:
        user.email = dados.email
    if dados.cnh is not None:
        user.cnh = dados.cnh
    if dados.senha is not None and dados.senha.strip():
        validar_senha(dados.senha)
        user.senha_hash = hash_password(dados.senha)

    user = salvar(db, user)
    return UsuarioOut.model_validate(user)


@app.delete("/api/usuarios/me", status_code=204)
def deletar_me(
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_usuario_from_token),
):
    # apagar viagens como motorista (ligadas às rotas)
    rotas = db.query(Rota).filter(Rota.motorista_id == user.id).all()
    for rota in rotas:
        db.query(Viagem).filter(Viagem.rota_id == rota.id).delete()
        db.delete(rota)

    # apagar viagens como passageiro
    db.query(Viagem).filter(Viagem.passageiro_id == user.id).delete()

    # apagar usuário
    db.delete(user)
    db.commit()



# ROTAS GERAIS (LISTAGEM DE ROTAS)


@app.get("/api/rotas", response_model=List[RotaOut])
def listar_rotas(
    origem: Optional[str] = None,
    destino: Optional[str] = None,
    dia: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Rota)

    if origem:
        q = q.filter(Rota.origem.ilike(f"%{origem}%"))
    if destino:
        q = q.filter(Rota.destino.ilike(f"%{destino}%"))
    if dia:
        q = q.filter(Rota.dias_semana.ilike(f"%{dia}%"))

    return [rota_to_out(r) for r in q.all()]



# ROTAS MOTORISTA (CRUD DE ROTAS)


@app.post("/api/motorista/rotas", response_model=RotaOut)
def criar_rota(
    rota: RotaCreate,
    db: Session = Depends(get_db),
    motorista: Usuario = Depends(get_motorista),
):
    dias_str = ",".join(rota.dias_semana)

    r = Rota(
        motorista_id=motorista.id,
        nome=rota.nome,
        origem=rota.origem,
        destino=rota.destino,
        hora_ida=rota.hora_ida,
        hora_volta=rota.hora_volta,
        vagas=rota.vagas,
        veiculo=rota.veiculo,
        dias_semana=dias_str,
        preco=rota.preco,
    )

    r = salvar(db, r)
    return rota_to_out(r)


@app.get("/api/motorista/minhas-rotas", response_model=List[RotaOut])
def minhas_rotas(
    db: Session = Depends(get_db),
    motorista: Usuario = Depends(get_motorista),
):
    rotas = db.query(Rota).filter(Rota.motorista_id == motorista.id).all()
    return [rota_to_out(r) for r in rotas]


@app.get("/api/motorista/rotas/{rota_id}", response_model=RotaOut)
def obter_rota_motorista(
    rota_id: int,
    db: Session = Depends(get_db),
    motorista: Usuario = Depends(get_motorista),
):
    rota = db.query(Rota).filter(
        Rota.id == rota_id,
        Rota.motorista_id == motorista.id,
    ).first()

    if not rota:
        raise HTTPException(status_code=404, detail="Rota não encontrada")

    return rota_to_out(rota)


@app.put("/api/motorista/rotas/{rota_id}", response_model=RotaOut)
def atualizar_rota(
    rota_id: int,
    dados: RotaUpdate,
    db: Session = Depends(get_db),
    motorista: Usuario = Depends(get_motorista),
):
    rota = db.query(Rota).filter(
        Rota.id == rota_id,
        Rota.motorista_id == motorista.id,
    ).first()

    if not rota:
        raise HTTPException(status_code=404, detail="Rota não encontrada")

    if dados.nome is not None:
        rota.nome = dados.nome
    if dados.origem is not None:
        rota.origem = dados.origem
    if dados.destino is not None:
        rota.destino = dados.destino
    if dados.hora_ida is not None:
        rota.hora_ida = dados.hora_ida
    if dados.hora_volta is not None:
        rota.hora_volta = dados.hora_volta
    if dados.vagas is not None:
        rota.vagas = dados.vagas
    if dados.veiculo is not None:
        rota.veiculo = dados.veiculo
    if dados.dias_semana is not None:
        rota.dias_semana = ",".join(dados.dias_semana)
    if dados.preco is not None:
        rota.preco = dados.preco

    rota = salvar(db, rota)
    return rota_to_out(rota)


@app.delete("/api/motorista/rotas/{rota_id}", status_code=204)
def deletar_rota(
    rota_id: int,
    db: Session = Depends(get_db),
    motorista: Usuario = Depends(get_motorista),
):
    rota = db.query(Rota).filter(
        Rota.id == rota_id,
        Rota.motorista_id == motorista.id,
    ).first()

    if not rota:
        raise HTTPException(status_code=404, detail="Rota não encontrada")

    db.query(Viagem).filter(Viagem.rota_id == rota.id).delete()
    db.delete(rota)
    db.commit()


@app.get("/api/motorista/resumo", response_model=MotoristaResumo)
def resumo_motorista(
    db: Session = Depends(get_db),
    motorista: Usuario = Depends(get_motorista),
):
    hoje = date.today()

    rotas_ativas = db.query(Rota).filter(
        Rota.motorista_id == motorista.id
    ).count()

    viagens_hoje = db.query(Viagem).join(Rota).filter(
        Rota.motorista_id == motorista.id,
        Viagem.data == hoje,
    ).count()

    alunos_hoje = db.query(Viagem.passageiro_id).join(Rota).filter(
        Rota.motorista_id == motorista.id,
        Viagem.data == hoje,
    ).distinct().count()

    return MotoristaResumo(
        rotas_ativas=rotas_ativas,
        viagens_hoje=viagens_hoje,
        alunos_hoje=alunos_hoje,
    )


@app.get("/api/motorista/viagens", response_model=List[ViagemOut])
def viagens_motorista(
    data_ref: Optional[date] = Query(None, alias="data"),
    db: Session = Depends(get_db),
    motorista: Usuario = Depends(get_motorista),
):
    q = db.query(Viagem).join(Rota).filter(Rota.motorista_id == motorista.id)

    if data_ref:
        q = q.filter(Viagem.data == data_ref)

    q = q.order_by(Viagem.data.asc())
    viagens = q.all()
    return [viagem_to_out(v) for v in viagens]


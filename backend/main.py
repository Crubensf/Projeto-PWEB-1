
from datetime import datetime, timedelta, date
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, status, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
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


# =========================
# CONFIG GERAL / AUTH
# =========================

SECRET_KEY = "Ablublé"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

origins = [
    "http://127.0.0.1:5500",
    "http://127.0.0.1:5501",
    "http://localhost:5500",
    "http://localhost:5501",
]

app = FastAPI(title="Van Já API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# HELPERS GERAIS
# =========================


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(sub: str, expires_delta: Optional[timedelta] = None):
    to_encode = {"sub": sub}
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=8))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_usuario_from_token(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise cred_exc
    except JWTError:
        raise cred_exc

    user = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    if user is None:
        raise cred_exc

    return user


def get_motorista(user=Depends(get_usuario_from_token)):
    if user.perfil != "motorista":
        raise HTTPException(status_code=403, detail="Apenas motoristas")
    return user


def get_estudante(user=Depends(get_usuario_from_token)):
    if user.perfil != "estudante":
        raise HTTPException(status_code=403, detail="Apenas estudantes")
    return user


# =========================
# HELPERS DE CONVERSÃO
# =========================


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
    r = v.rota
    rota_out = rota_to_out(r)
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
    nome: str = Form(...),
    email: EmailStr = Form(...),
    senha: str = Form(...),
    perfil: str = Form(...),
    cnh: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    from pydantic import EmailStr  # import local para o tipo do parâmetro (ou mova pro topo)

    if db.query(Usuario).filter(Usuario.email == email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    user = Usuario(
        nome=nome,
        email=email,
        senha_hash=hash_password(senha),
        perfil=perfil,
        cnh=cnh,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(sub=str(user.id))
    return Token(access_token=token, usuario=UsuarioOut.model_validate(user))


@app.post("/api/auth/login", response_model=Token)
def login(data: LoginData, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == data.email).first()

    if not user or not verify_password(data.senha, user.senha_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    token = create_access_token(sub=str(user.id))
    return Token(access_token=token, usuario=UsuarioOut.model_validate(user))


# =========================
# ROTAS USUÁRIO (CRUD)
# =========================


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
        user.senha_hash = hash_password(dados.senha)

    db.add(user)
    db.commit()
    db.refresh(user)

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
    # 204 sem conteúdo


# =========================
# ROTAS GERAIS (LISTAGEM DE ROTAS)
# =========================


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


# =========================
# ROTAS MOTORISTA (CRUD DE ROTAS)
# =========================


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

    db.add(r)
    db.commit()
    db.refresh(r)

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
        Rota.motorista_id == motorista.id
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
        Rota.motorista_id == motorista.id
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

    db.add(rota)
    db.commit()
    db.refresh(rota)

    return rota_to_out(rota)


@app.delete("/api/motorista/rotas/{rota_id}", status_code=204)
def deletar_rota(
    rota_id: int,
    db: Session = Depends(get_db),
    motorista: Usuario = Depends(get_motorista),
):
    rota = db.query(Rota).filter(
        Rota.id == rota_id,
        Rota.motorista_id == motorista.id
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
        Viagem.data == hoje
    ).count()

    alunos_hoje = db.query(Viagem.passageiro_id).join(Rota).filter(
        Rota.motorista_id == motorista.id,
        Viagem.data == hoje
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


# =========================
# ROTAS PASSAGEIRO (CRUD DE VIAGENS)
# =========================


@app.post("/api/passageiro/viagens", response_model=ViagemOut)
def reservar_viagem(
    data_in: ViagemCreate,
    db: Session = Depends(get_db),
    estudante: Usuario = Depends(get_estudante),
):
    rota = db.query(Rota).filter(Rota.id == data_in.rota_id).first()
    if not rota:
        raise HTTPException(status_code=404, detail="Rota não encontrada")

    reservas = db.query(Viagem).filter(
        Viagem.rota_id == rota.id,
        Viagem.data == data_in.data,
        Viagem.status != "cancelada"
    ).count()

    if reservas >= rota.vagas:
        raise HTTPException(status_code=400, detail="Não há vagas disponíveis")

    v = Viagem(
        rota_id=rota.id,
        passageiro_id=estudante.id,
        data=data_in.data
    )

    db.add(v)
    db.commit()
    db.refresh(v)

    return viagem_to_out(v)


@app.get("/api/passageiro/viagens/proximas", response_model=List[ViagemOut])
def viagens_proximas(
    db: Session = Depends(get_db),
    estudante: Usuario = Depends(get_estudante),
):
    hoje = date.today()

    q = db.query(Viagem).join(Rota).filter(
        Viagem.passageiro_id == estudante.id,
        Viagem.data >= hoje,
        Viagem.status != "cancelada"
    ).order_by(Viagem.data.asc())

    viagens = q.all()
    return [viagem_to_out(v) for v in viagens]


@app.get("/api/passageiro/viagens/historico", response_model=List[ViagemOut])
def viagens_historico(
    db: Session = Depends(get_db),
    estudante: Usuario = Depends(get_estudante),
):
    hoje = date.today()

    q = db.query(Viagem).join(Rota).filter(
        Viagem.passageiro_id == estudante.id,
        Viagem.data < hoje
    ).order_by(Viagem.data.desc())

    viagens = q.all()
    return [viagem_to_out(v) for v in viagens]


@app.patch("/api/passageiro/viagens/{viagem_id}", response_model=ViagemOut)
def atualizar_viagem_passageiro(
    viagem_id: int,
    dados: ViagemUpdate,
    db: Session = Depends(get_db),
    estudante: Usuario = Depends(get_estudante),
):
    v = db.query(Viagem).filter(
        Viagem.id == viagem_id,
        Viagem.passageiro_id == estudante.id
    ).first()

    if not v:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")

    if dados.status is not None:
        v.status = dados.status

    db.add(v)
    db.commit()
    db.refresh(v)

    return viagem_to_out(v)


@app.delete("/api/passageiro/viagens/{viagem_id}", status_code=204)
def deletar_viagem_passageiro(
    viagem_id: int,
    db: Session = Depends(get_db),
    estudante: Usuario = Depends(get_estudante),
):
    v = db.query(Viagem).filter(
        Viagem.id == viagem_id,
        Viagem.passageiro_id == estudante.id
    ).first()

    if not v:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")

    db.delete(v)
    db.commit()

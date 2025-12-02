from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta, date

from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Date, DateTime, Float
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session

from passlib.context import CryptContext
from jose import jwt, JWTError

# =========================
# CONFIG GERAL / DB / AUTH
# =========================

SQLALCHEMY_DATABASE_URL = "sqlite:///./vanja.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

SECRET_KEY = "troca-essa-string-por-uma-bem-grande-e-secreta"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(sub: str, expires_delta: Optional[timedelta] = None):
    to_encode = {"sub": sub}
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=8))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_usuario_from_token(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
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


def get_motorista(user = Depends(get_usuario_from_token)):
    if user.perfil != "motorista":
        raise HTTPException(status_code=403, detail="Apenas motoristas")
    return user


def get_estudante(user = Depends(get_usuario_from_token)):
    if user.perfil != "estudante":
        raise HTTPException(status_code=403, detail="Apenas estudantes")
    return user


# ============
# MODELOS DB
# ============

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    perfil = Column(String, nullable=False)  # estudante | motorista

    cnh = Column(String, nullable=True)
    cnh_imagem_path = Column(String, nullable=True)
    doc_veiculo_imagem_path = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    rotas = relationship("Rota", back_populates="motorista")
    viagens = relationship("Viagem", back_populates="passageiro")


class Rota(Base):
    __tablename__ = "rotas"

    id = Column(Integer, primary_key=True, index=True)
    motorista_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    nome = Column(String, nullable=False)
    origem = Column(String, nullable=False)
    destino = Column(String, nullable=False)
    hora_ida = Column(String, nullable=False)
    hora_volta = Column(String, nullable=True)
    vagas = Column(Integer, nullable=False)
    veiculo = Column(String, nullable=True)

    dias_semana = Column(String, nullable=False)  # "segunda,terça,quarta"
    preco = Column(Float, nullable=False)
    imagem_path = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    motorista = relationship("Usuario", back_populates="rotas")
    viagens = relationship("Viagem", back_populates="rota")


class Viagem(Base):
    __tablename__ = "viagens"

    id = Column(Integer, primary_key=True, index=True)
    rota_id = Column(Integer, ForeignKey("rotas.id"), nullable=False)
    passageiro_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    data = Column(Date, nullable=False)
    status = Column(String, default="reservada")  # reservada, concluida, cancelada

    created_at = Column(DateTime, default=datetime.utcnow)

    rota = relationship("Rota", back_populates="viagens")
    passageiro = relationship("Usuario", back_populates="viagens")


# ============
# SCHEMAS API
# ============

class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr
    perfil: str  # estudante | motorista


class UsuarioCreate(UsuarioBase):
    senha: str
    cnh: Optional[str] = None


class UsuarioOut(UsuarioBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class LoginData(BaseModel):
    email: EmailStr
    senha: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut


class RotaBase(BaseModel):
    nome: str
    origem: str
    destino: str
    hora_ida: str
    hora_volta: Optional[str] = None
    vagas: int
    veiculo: Optional[str] = None
    dias_semana: List[str]
    preco: float


class RotaCreate(RotaBase):
    pass


class RotaOut(RotaBase):
    id: int
    motorista_id: int

    class Config:
        from_attributes = True


class ViagemBase(BaseModel):
    rota_id: int
    data: date


class ViagemCreate(ViagemBase):
    pass


class ViagemOut(BaseModel):
    id: int
    rota: RotaOut
    data: date
    status: str

    class Config:
        from_attributes = True


class MotoristaResumo(BaseModel):
    rotas_ativas: int
    viagens_hoje: int
    alunos_hoje: int


# ============
# APP FASTAPI
# ============

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Van Já API (simples)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # depois você pode restringir pro domínio do front
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============
# ROTAS AUTH
# ============

@app.post("/api/auth/register", response_model=Token)
async def registrar_usuario(
    nome: str = Form(...),
    email: EmailStr = Form(...),
    senha: str = Form(...),
    perfil: str = Form(...),  # estudante | motorista
    cnh: Optional[str] = Form(None),
    cnh_imagem: Optional[UploadFile] = File(None),
    doc_veiculo_imagem: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    # já existe?
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

    # aqui você poderia salvar as imagens em disco
    # e atualizar user.cnh_imagem_path / user.doc_veiculo_imagem_path

    access_token = create_access_token(sub=str(user.id))
    usuario_out = UsuarioOut.from_orm(user)
    return Token(access_token=access_token, usuario=usuario_out)


@app.post("/api/auth/login", response_model=Token)
def login(data: LoginData, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == data.email).first()
    if not user or not verify_password(data.senha, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )

    access_token = create_access_token(sub=str(user.id))
    usuario_out = UsuarioOut.from_orm(user)
    return Token(access_token=access_token, usuario=usuario_out)


# ============
# ROTAS – GERAL
# ============

@app.get("/api/rotas", response_model=List[RotaOut])
def listar_rotas(
    origem: Optional[str] = Query(None),
    destino: Optional[str] = Query(None),
    dia: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Rota)

    if origem:
        q = q.filter(Rota.origem.ilike(f"%{origem}%"))
    if destino:
        q = q.filter(Rota.destino.ilike(f"%{destino}%"))
    if dia:
        like = f"%{dia.lower()}%"
        q = q.filter(Rota.dias_semana.ilike(like))

    rotas = q.all()
    return rotas


# ============
# ROTAS – MOTORISTA
# ============

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
    return r


@app.get("/api/motorista/minhas-rotas", response_model=List[RotaOut])
def minhas_rotas(
    db: Session = Depends(get_db),
    motorista: Usuario = Depends(get_motorista),
):
    rotas = db.query(Rota).filter(Rota.motorista_id == motorista.id).all()
    return rotas


@app.get("/api/motorista/resumo", response_model=MotoristaResumo)
def resumo_motorista(
    db: Session = Depends(get_db),
    motorista: Usuario = Depends(get_motorista),
):
    hoje = date.today()

    rotas_ativas = db.query(Rota).filter(Rota.motorista_id == motorista.id).count()

    viagens_hoje = (
        db.query(Viagem)
        .join(Rota)
        .filter(Rota.motorista_id == motorista.id, Viagem.data == hoje)
        .count()
    )

    alunos_hoje = (
        db.query(Viagem.passageiro_id)
        .join(Rota)
        .filter(Rota.motorista_id == motorista.id, Viagem.data == hoje)
        .distinct()
        .count()
    )

    return MotoristaResumo(
        rotas_ativas=rotas_ativas,
        viagens_hoje=viagens_hoje,
        alunos_hoje=alunos_hoje,
    )


@app.get("/api/motorista/viagens")
def viagens_por_dia(
    data: date,
    db: Session = Depends(get_db),
    motorista: Usuario = Depends(get_motorista),
):
    viagens = (
        db.query(Viagem)
        .join(Rota)
        .filter(Rota.motorista_id == motorista.id, Viagem.data == data)
        .all()
    )
    # aqui você pode depois criar um schema específico
    return viagens


# ============
# ROTAS – PASSAGEIRO
# ============

@app.post("/api/passageiro/viagens", response_model=ViagemOut)
def reservar_viagem(
    data: ViagemCreate,
    db: Session = Depends(get_db),
    estudante: Usuario = Depends(get_estudante),
):
    rota = db.query(Rota).filter(Rota.id == data.rota_id).first()
    if not rota:
        raise HTTPException(status_code=404, detail="Rota não encontrada")

    reservas = (
        db.query(Viagem)
        .filter(
            Viagem.rota_id == rota.id,
            Viagem.data == data.data,
            Viagem.status != "cancelada",
        )
        .count()
    )

    if reservas >= rota.vagas:
        raise HTTPException(
            status_code=400, detail="Não há vagas disponíveis para esta data"
        )

    v = Viagem(
        rota_id=rota.id,
        passageiro_id=estudante.id,
        data=data.data,
        status="reservada",
    )

    db.add(v)
    db.commit()
    db.refresh(v)

    # precisa embrulhar rota dentro de ViagemOut
    rota_out = RotaOut(
        id=rota.id,
        motorista_id=rota.motorista_id,
        nome=rota.nome,
        origem=rota.origem,
        destino=rota.destino,
        hora_ida=rota.hora_ida,
        hora_volta=rota.hora_volta,
        vagas=rota.vagas,
        veiculo=rota.veiculo,
        dias_semana=rota.dias_semana.split(","),
        preco=rota.preco,
    )

    return ViagemOut(
        id=v.id,
        rota=rota_out,
        data=v.data,
        status=v.status,
    )


@app.get("/api/passageiro/viagens/proximas", response_model=List[ViagemOut])
def viagens_proximas(
    db: Session = Depends(get_db),
    estudante: Usuario = Depends(get_estudante),
):
    hoje = date.today()
    viagens = (
        db.query(Viagem)
        .join(Rota)
        .filter(
            Viagem.passageiro_id == estudante.id,
            Viagem.data >= hoje,
            Viagem.status != "cancelada",
        )
        .order_by(Viagem.data.asc())
        .all()
    )

    result: List[ViagemOut] = []
    for v in viagens:
        rota = v.rota
        rota_out = RotaOut(
            id=rota.id,
            motorista_id=rota.motorista_id,
            nome=rota.nome,
            origem=rota.origem,
            destino=rota.destino,
            hora_ida=rota.hora_ida,
            hora_volta=rota.hora_volta,
            vagas=rota.vagas,
            veiculo=rota.veiculo,
            dias_semana=rota.dias_semana.split(","),
            preco=rota.preco,
        )
        result.append(
            ViagemOut(id=v.id, rota=rota_out, data=v.data, status=v.status)
        )

    return result


@app.get("/api/passageiro/viagens/historico", response_model=List[ViagemOut])
def viagens_historico(
    db: Session = Depends(get_db),
    estudante: Usuario = Depends(get_estudante),
):
    hoje = date.today()
    viagens = (
        db.query(Viagem)
        .join(Rota)
        .filter(
            Viagem.passageiro_id == estudante.id,
            Viagem.data < hoje,
        )
        .order_by(Viagem.data.desc())
        .all()
    )

    result: List[ViagemOut] = []
    for v in viagens:
        rota = v.rota
        rota_out = RotaOut(
            id=rota.id,
            motorista_id=rota.motorista_id,
            nome=rota.nome,
            origem=rota.origem,
            destino=rota.destino,
            hora_ida=rota.hora_ida,
            hora_volta=rota.hora_volta,
            vagas=rota.vagas,
            veiculo=rota.veiculo,
            dias_semana=rota.dias_semana.split(","),
            preco=rota.preco,
        )
        result.append(
            ViagemOut(id=v.id, rota=rota_out, data=v.data, status=v.status)
        )

    return result


# ============
# ROTA /ME
# ============

@app.get("/api/usuarios/me", response_model=UsuarioOut)
def me(user = Depends(get_usuario_from_token)):
    return UsuarioOut.from_orm(user)

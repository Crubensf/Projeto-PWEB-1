from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Padrões de validação reusados
HORA_PATTERN = r"^\d{2}:\d{2}$"
Perfil = Literal["estudante", "motorista"]
DiaSemana = Literal["seg", "ter", "qua", "qui", "sex", "sab", "dom"]


# ============ USUÁRIO ============


class UsuarioBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=120)
    email: EmailStr = Field(..., max_length=120)
    perfil: Perfil


class UsuarioOut(UsuarioBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UsuarioCreate(UsuarioBase):
    senha: str = Field(..., min_length=8, max_length=200)
    cnh: str | None = Field(None, pattern=r"^\d{11}$")


class UsuarioUpdate(BaseModel):
    nome: str | None = Field(None, min_length=2, max_length=120)
    email: EmailStr | None = Field(None, max_length=120)
    senha: str | None = Field(None, min_length=8, max_length=200)
    cnh: str | None = Field(None, pattern=r"^\d{11}$")


class LoginData(BaseModel):
    email: EmailStr = Field(..., max_length=120)
    senha: str = Field(..., min_length=1, max_length=200)


class Token(BaseModel):
    # O token JWT vai exclusivamente no cookie HttpOnly — não retorna no body
    # para preservar a garantia do HttpOnly (token inacessível ao JavaScript).
    usuario: UsuarioOut


# ============ ROTAS / ROTAS (MOTORISTA) ============


class RotaBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=120)
    origem: str = Field(..., min_length=2, max_length=120)
    destino: str = Field(..., min_length=2, max_length=120)
    origem_lat: float | None = Field(None, ge=-90, le=90)
    origem_lng: float | None = Field(None, ge=-180, le=180)
    destino_lat: float | None = Field(None, ge=-90, le=90)
    destino_lng: float | None = Field(None, ge=-180, le=180)
    hora_ida: str = Field(..., pattern=HORA_PATTERN)
    hora_volta: str | None = Field(None, pattern=HORA_PATTERN)
    vagas: int = Field(..., ge=1, le=99)
    veiculo: str | None = Field(None, max_length=30)
    dias_semana: list[DiaSemana] = Field(..., min_length=1, max_length=7)
    preco: float = Field(..., ge=0, le=10000)


class RotaCreate(RotaBase):
    pass


class RotaUpdate(BaseModel):
    nome: str | None = Field(None, min_length=2, max_length=120)
    origem: str | None = Field(None, min_length=2, max_length=120)
    destino: str | None = Field(None, min_length=2, max_length=120)
    origem_lat: float | None = Field(None, ge=-90, le=90)
    origem_lng: float | None = Field(None, ge=-180, le=180)
    destino_lat: float | None = Field(None, ge=-90, le=90)
    destino_lng: float | None = Field(None, ge=-180, le=180)
    hora_ida: str | None = Field(None, pattern=HORA_PATTERN)
    hora_volta: str | None = Field(None, pattern=HORA_PATTERN)
    vagas: int | None = Field(None, ge=1, le=99)
    veiculo: str | None = Field(None, max_length=30)
    dias_semana: list[DiaSemana] | None = Field(None, min_length=1, max_length=7)
    preco: float | None = Field(None, ge=0, le=10000)


class MotoristaResumoCard(BaseModel):
    """Subconjunto público do motorista embutido em cards de rota."""

    id: int
    nome: str
    media_avaliacoes: float | None = None
    total_avaliacoes: int = 0


class RotaOut(RotaBase):
    id: int
    motorista_id: int
    motorista: MotoristaResumoCard | None = None
    # Estimativas calculadas a partir das coordenadas (None se não houver geo)
    duracao_estimada_min: int | None = None
    hora_chegada_estimada: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RotasListagem(BaseModel):
    items: list[RotaOut]
    total: int
    limit: int
    offset: int


OrdenarRotaPor = Literal["preco_asc", "preco_desc", "hora_asc", "recentes"]


# ============ VIAGENS (PASSAGEIRO) ============

StatusViagem = Literal["reservada", "realizada", "cancelada"]
# Estudante só pode atingir esses dois status; "realizada" é prerrogativa do motorista
StatusViagemMotorista = Literal["realizada", "cancelada"]


class ViagemCreate(BaseModel):
    rota_id: int
    data: date


class ViagemStatusUpdate(BaseModel):
    status: StatusViagemMotorista


class ViagemOut(BaseModel):
    id: int
    rota: RotaOut
    data: date
    status: StatusViagem
    passageiro_id: int
    avaliada: bool = False


# ============ AVALIAÇÕES ============


class AvaliacaoCreate(BaseModel):
    nota: int = Field(..., ge=1, le=5)
    comentario: str | None = Field(None, max_length=500)


class AvaliacaoOut(BaseModel):
    id: int
    nota: int
    comentario: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MotoristaPublicoOut(BaseModel):
    id: int
    nome: str
    media_avaliacoes: float | None = None
    total_avaliacoes: int = 0


# ============ RESUMO MOTORISTA ============


class MotoristaResumo(BaseModel):
    rotas_ativas: int
    viagens_hoje: int
    alunos_hoje: int

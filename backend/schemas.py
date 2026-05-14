
from datetime import datetime, date
from typing import Optional, List, Literal

from pydantic import BaseModel, EmailStr, Field


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

    class Config:
        from_attributes = True


class UsuarioCreate(UsuarioBase):
    senha: str = Field(..., min_length=6, max_length=200)
    cnh: Optional[str] = Field(None, pattern=r"^\d{11}$")


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2, max_length=120)
    email: Optional[EmailStr] = Field(None, max_length=120)
    senha: Optional[str] = Field(None, min_length=6, max_length=200)
    cnh: Optional[str] = Field(None, pattern=r"^\d{11}$")


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
    hora_ida: str = Field(..., pattern=HORA_PATTERN)
    hora_volta: Optional[str] = Field(None, pattern=HORA_PATTERN)
    vagas: int = Field(..., ge=1, le=99)
    veiculo: Optional[str] = Field(None, max_length=30)
    dias_semana: List[DiaSemana] = Field(..., min_length=1, max_length=7)
    preco: float = Field(..., ge=0, le=10000)


class RotaCreate(RotaBase):
    pass


class RotaUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2, max_length=120)
    origem: Optional[str] = Field(None, min_length=2, max_length=120)
    destino: Optional[str] = Field(None, min_length=2, max_length=120)
    hora_ida: Optional[str] = Field(None, pattern=HORA_PATTERN)
    hora_volta: Optional[str] = Field(None, pattern=HORA_PATTERN)
    vagas: Optional[int] = Field(None, ge=1, le=99)
    veiculo: Optional[str] = Field(None, max_length=30)
    dias_semana: Optional[List[DiaSemana]] = Field(None, min_length=1, max_length=7)
    preco: Optional[float] = Field(None, ge=0, le=10000)


class RotaOut(RotaBase):
    id: int
    motorista_id: int

    class Config:
        from_attributes = True


# ============ VIAGENS (PASSAGEIRO) ============

class ViagemCreate(BaseModel):
    rota_id: int
    data: date


class ViagemUpdate(BaseModel):
    status: Optional[str] = None


class ViagemOut(BaseModel):
    id: int
    rota: RotaOut
    data: date
    status: str


# ============ RESUMO MOTORISTA ============

class MotoristaResumo(BaseModel):
    rotas_ativas: int
    viagens_hoje: int
    alunos_hoje: int

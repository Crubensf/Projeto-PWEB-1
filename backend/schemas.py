# backend/schemas.py
from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, EmailStr


# ============ USUÁRIO ============

class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr
    perfil: str


class UsuarioOut(UsuarioBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True  # (equivalente ao antigo orm_mode)


class UsuarioCreate(UsuarioBase):
    senha: str
    cnh: Optional[str] = None


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    senha: Optional[str] = None
    cnh: Optional[str] = None


class LoginData(BaseModel):
    email: EmailStr
    senha: str


class Token(BaseModel):
    access_token: str
    usuario: UsuarioOut


# ============ ROTAS / ROTAS (MOTORISTA) ============

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


class RotaUpdate(BaseModel):
    nome: Optional[str] = None
    origem: Optional[str] = None
    destino: Optional[str] = None
    hora_ida: Optional[str] = None
    hora_volta: Optional[str] = None
    vagas: Optional[int] = None
    veiculo: Optional[str] = None
    dias_semana: Optional[List[str]] = None
    preco: Optional[float] = None


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

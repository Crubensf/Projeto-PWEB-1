
from datetime import datetime, date

from sqlalchemy import (
    Column, Integer, String, ForeignKey, Date, DateTime, Float
)
from sqlalchemy.orm import relationship

from db import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    perfil = Column(String, nullable=False)

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

    dias_semana = Column(String, nullable=False)
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
    status = Column(String, default="reservada")

    created_at = Column(DateTime, default=datetime.utcnow)

    rota = relationship("Rota", back_populates="viagens")
    passageiro = relationship("Usuario", back_populates="viagens")

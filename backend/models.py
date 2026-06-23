from datetime import UTC, datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


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

    created_at = Column(DateTime, default=_utcnow)

    rotas = relationship("Rota", back_populates="motorista")
    viagens = relationship("Viagem", back_populates="passageiro")


class Rota(Base):
    __tablename__ = "rotas"

    id = Column(Integer, primary_key=True, index=True)
    motorista_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    nome = Column(String, nullable=False)
    origem = Column(String, nullable=False, index=True)
    destino = Column(String, nullable=False, index=True)
    # Versões sem acento/caixa para busca (preenchidas na criação/atualização)
    origem_norm = Column(String, nullable=True, index=True)
    destino_norm = Column(String, nullable=True, index=True)
    origem_lat = Column(Float, nullable=True)
    origem_lng = Column(Float, nullable=True)
    destino_lat = Column(Float, nullable=True)
    destino_lng = Column(Float, nullable=True)
    hora_ida = Column(String, nullable=False)
    hora_volta = Column(String, nullable=True)
    vagas = Column(Integer, nullable=False)
    veiculo = Column(String, nullable=True)

    dias_semana = Column(String, nullable=False, index=True)
    preco = Column(Float, nullable=False)
    imagem_path = Column(String, nullable=True)

    created_at = Column(DateTime, default=_utcnow)

    motorista = relationship("Usuario", back_populates="rotas")
    viagens = relationship("Viagem", back_populates="rota")


class Viagem(Base):
    __tablename__ = "viagens"

    id = Column(Integer, primary_key=True, index=True)
    rota_id = Column(Integer, ForeignKey("rotas.id"), nullable=False)
    passageiro_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    data = Column(Date, nullable=False, index=True)
    status = Column(String, default="reservada", nullable=False, index=True)

    created_at = Column(DateTime, default=_utcnow)

    rota = relationship("Rota", back_populates="viagens")
    passageiro = relationship("Usuario", back_populates="viagens")
    avaliacao = relationship(
        "Avaliacao", back_populates="viagem", uselist=False, cascade="all, delete-orphan"
    )


class Avaliacao(Base):
    __tablename__ = "avaliacoes"

    id = Column(Integer, primary_key=True, index=True)
    viagem_id = Column(Integer, ForeignKey("viagens.id"), unique=True, nullable=False, index=True)
    nota = Column(Integer, nullable=False)
    comentario = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    viagem = relationship("Viagem", back_populates="avaliacao")


class EventoAuditoria(Base):
    __tablename__ = "eventos_auditoria"

    id = Column(Integer, primary_key=True, index=True)
    # usuario_id é nullable: registramos tentativas anônimas de login também
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    tipo = Column(String, nullable=False, index=True)
    ip = Column(String, nullable=True)
    detalhe = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow, index=True)

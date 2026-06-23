from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import auditoria
import cache
from config import settings
from db import get_db
from deps import get_motorista
from models import Rota, Usuario, Viagem
from schemas import (
    OrdenarRotaPor,
    RotaCreate,
    RotaOut,
    RotasListagem,
    RotaUpdate,
)
from serializers import rota_to_out
from text_utils import normalizar

CACHE_NS_ROTAS = "rotas_publicas"


# Listagem pública de rotas
public_router = APIRouter(prefix="/api/rotas", tags=["rotas"])

# CRUD e listagem das próprias rotas do motorista
motorista_router = APIRouter(prefix="/api/motorista", tags=["motorista"])


_HORA_RE = r"^\d{2}:\d{2}$"


@public_router.get("", response_model=RotasListagem)
def listar_rotas(
    origem: str | None = None,
    destino: str | None = None,
    dia: str | None = None,
    preco_min: float | None = Query(None, ge=0),
    preco_max: float | None = Query(None, ge=0),
    hora_min: str | None = Query(None, pattern=_HORA_RE),
    hora_max: str | None = Query(None, pattern=_HORA_RE),
    ordenar_por: OrdenarRotaPor = "recentes",
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    params = {
        "origem": origem,
        "destino": destino,
        "dia": dia,
        "preco_min": preco_min,
        "preco_max": preco_max,
        "hora_min": hora_min,
        "hora_max": hora_max,
        "ordenar_por": ordenar_por,
        "limit": limit,
        "offset": offset,
    }
    cached = cache.cache_get(CACHE_NS_ROTAS, params)
    if cached is not None:
        return cached

    q = db.query(Rota)

    if origem:
        q = q.filter(Rota.origem_norm.ilike(f"%{normalizar(origem)}%"))
    if destino:
        q = q.filter(Rota.destino_norm.ilike(f"%{normalizar(destino)}%"))
    if dia:
        q = q.filter(Rota.dias_semana.ilike(f"%{dia}%"))
    if preco_min is not None:
        q = q.filter(Rota.preco >= preco_min)
    if preco_max is not None:
        q = q.filter(Rota.preco <= preco_max)
    if hora_min:
        q = q.filter(Rota.hora_ida >= hora_min)
    if hora_max:
        q = q.filter(Rota.hora_ida <= hora_max)

    if ordenar_por == "preco_asc":
        q = q.order_by(Rota.preco.asc(), Rota.id.desc())
    elif ordenar_por == "preco_desc":
        q = q.order_by(Rota.preco.desc(), Rota.id.desc())
    elif ordenar_por == "hora_asc":
        q = q.order_by(Rota.hora_ida.asc(), Rota.id.desc())
    else:
        q = q.order_by(Rota.created_at.desc(), Rota.id.desc())

    total = q.count()
    rotas = q.offset(offset).limit(limit).all()

    resposta = RotasListagem(
        items=[rota_to_out(r, db=db) for r in rotas],
        total=total,
        limit=limit,
        offset=offset,
    )
    cache.cache_set(
        CACHE_NS_ROTAS,
        params,
        resposta.model_dump(mode="json"),
        ttl_s=settings.cache_rotas_ttl_s,
    )
    return resposta


@motorista_router.post("/rotas", response_model=RotaOut)
def criar_rota(
    rota: RotaCreate,
    db: Session = Depends(get_db),
    motorista: Usuario = Depends(get_motorista),
):
    r = Rota(
        motorista_id=motorista.id,
        nome=rota.nome,
        origem=rota.origem,
        destino=rota.destino,
        origem_norm=normalizar(rota.origem),
        destino_norm=normalizar(rota.destino),
        origem_lat=rota.origem_lat,
        origem_lng=rota.origem_lng,
        destino_lat=rota.destino_lat,
        destino_lng=rota.destino_lng,
        hora_ida=rota.hora_ida,
        hora_volta=rota.hora_volta,
        vagas=rota.vagas,
        veiculo=rota.veiculo,
        dias_semana=",".join(rota.dias_semana),
        preco=rota.preco,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    cache.cache_invalidate(CACHE_NS_ROTAS)
    auditoria.log_evento(
        db,
        auditoria.ROTA_CRIADA,
        usuario_id=motorista.id,
        detalhe=f"rota_id={r.id}",
    )
    return rota_to_out(r)


@motorista_router.get("/minhas-rotas", response_model=list[RotaOut])
def minhas_rotas(
    db: Session = Depends(get_db),
    motorista: Usuario = Depends(get_motorista),
):
    rotas = db.query(Rota).filter(Rota.motorista_id == motorista.id).all()
    return [rota_to_out(r) for r in rotas]


@motorista_router.get("/rotas/{rota_id}", response_model=RotaOut)
def obter_rota(
    rota_id: int,
    db: Session = Depends(get_db),
    motorista: Usuario = Depends(get_motorista),
):
    rota = (
        db.query(Rota)
        .filter(
            Rota.id == rota_id,
            Rota.motorista_id == motorista.id,
        )
        .first()
    )
    if not rota:
        raise HTTPException(status_code=404, detail="Rota não encontrada")
    return rota_to_out(rota)


@motorista_router.put("/rotas/{rota_id}", response_model=RotaOut)
def atualizar_rota(
    rota_id: int,
    dados: RotaUpdate,
    db: Session = Depends(get_db),
    motorista: Usuario = Depends(get_motorista),
):
    rota = (
        db.query(Rota)
        .filter(
            Rota.id == rota_id,
            Rota.motorista_id == motorista.id,
        )
        .first()
    )
    if not rota:
        raise HTTPException(status_code=404, detail="Rota não encontrada")

    if dados.nome is not None:
        rota.nome = dados.nome
    if dados.origem is not None:
        rota.origem = dados.origem
        rota.origem_norm = normalizar(dados.origem)
    if dados.destino is not None:
        rota.destino = dados.destino
        rota.destino_norm = normalizar(dados.destino)
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
    for campo in ("origem_lat", "origem_lng", "destino_lat", "destino_lng"):
        v = getattr(dados, campo)
        if v is not None:
            setattr(rota, campo, v)

    db.add(rota)
    db.commit()
    db.refresh(rota)
    cache.cache_invalidate(CACHE_NS_ROTAS)
    return rota_to_out(rota)


@motorista_router.delete("/rotas/{rota_id}", status_code=204)
def deletar_rota(
    rota_id: int,
    db: Session = Depends(get_db),
    motorista: Usuario = Depends(get_motorista),
):
    rota = (
        db.query(Rota)
        .filter(
            Rota.id == rota_id,
            Rota.motorista_id == motorista.id,
        )
        .first()
    )
    if not rota:
        raise HTTPException(status_code=404, detail="Rota não encontrada")

    db.query(Viagem).filter(Viagem.rota_id == rota.id).delete()
    db.delete(rota)
    db.commit()
    cache.cache_invalidate(CACHE_NS_ROTAS)
    auditoria.log_evento(
        db,
        auditoria.ROTA_DELETADA,
        usuario_id=motorista.id,
        detalhe=f"rota_id={rota_id}",
    )

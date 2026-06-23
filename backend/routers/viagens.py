from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import auditoria
from db import get_db
from deps import get_motorista
from models import Rota, Usuario, Viagem
from schemas import MotoristaResumo, ViagemOut, ViagemStatusUpdate
from serializers import viagem_to_out

router = APIRouter(prefix="/api/motorista", tags=["motorista"])


@router.get("/resumo", response_model=MotoristaResumo)
def resumo_motorista(
    db: Session = Depends(get_db),
    motorista: Usuario = Depends(get_motorista),
):
    hoje = date.today()

    rotas_ativas = db.query(Rota).filter(Rota.motorista_id == motorista.id).count()

    viagens_hoje = (
        db.query(Viagem)
        .join(Rota)
        .filter(
            Rota.motorista_id == motorista.id,
            Viagem.data == hoje,
        )
        .count()
    )

    alunos_hoje = (
        db.query(Viagem.passageiro_id)
        .join(Rota)
        .filter(
            Rota.motorista_id == motorista.id,
            Viagem.data == hoje,
        )
        .distinct()
        .count()
    )

    return MotoristaResumo(
        rotas_ativas=rotas_ativas,
        viagens_hoje=viagens_hoje,
        alunos_hoje=alunos_hoje,
    )


@router.get("/viagens", response_model=list[ViagemOut])
def viagens_motorista(
    data_ref: date | None = Query(None, alias="data"),
    db: Session = Depends(get_db),
    motorista: Usuario = Depends(get_motorista),
):
    q = db.query(Viagem).join(Rota).filter(Rota.motorista_id == motorista.id)
    if data_ref:
        q = q.filter(Viagem.data == data_ref)
    q = q.order_by(Viagem.data.asc())
    return [viagem_to_out(v, db=db) for v in q.all()]


@router.put("/viagens/{viagem_id}", response_model=ViagemOut)
def atualizar_status_viagem(
    viagem_id: int,
    dados: ViagemStatusUpdate,
    db: Session = Depends(get_db),
    motorista: Usuario = Depends(get_motorista),
):
    v = (
        db.query(Viagem)
        .join(Rota)
        .filter(Viagem.id == viagem_id, Rota.motorista_id == motorista.id)
        .first()
    )
    if not v:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")

    if v.status != "reservada":
        raise HTTPException(
            status_code=400,
            detail="Esta viagem já foi finalizada.",
        )

    v.status = dados.status
    db.add(v)
    db.commit()
    db.refresh(v)
    auditoria.log_evento(
        db,
        auditoria.VIAGEM_STATUS_ATUALIZADO,
        usuario_id=motorista.id,
        detalhe=f"viagem_id={v.id} status={v.status}",
    )
    return viagem_to_out(v, db=db)

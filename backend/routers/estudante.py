from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import auditoria
from db import get_db
from deps import get_estudante
from models import Avaliacao, Rota, Usuario, Viagem
from schemas import AvaliacaoCreate, AvaliacaoOut, ViagemCreate, ViagemOut
from serializers import viagem_to_out
from viagens_service import validar_reserva

router = APIRouter(prefix="/api/estudante", tags=["estudante"])


@router.get("/viagens", response_model=list[ViagemOut])
def listar_minhas_viagens(
    db: Session = Depends(get_db),
    estudante: Usuario = Depends(get_estudante),
):
    viagens = (
        db.query(Viagem)
        .filter(Viagem.passageiro_id == estudante.id)
        .order_by(Viagem.data.desc())
        .all()
    )
    return [viagem_to_out(v, db=db) for v in viagens]


@router.post("/viagens", response_model=ViagemOut, status_code=201)
def reservar_viagem(
    dados: ViagemCreate,
    db: Session = Depends(get_db),
    estudante: Usuario = Depends(get_estudante),
):
    rota = db.query(Rota).filter(Rota.id == dados.rota_id).first()
    if not rota:
        raise HTTPException(status_code=404, detail="Rota não encontrada")

    validar_reserva(db, rota, dados.data, estudante.id)

    v = Viagem(
        rota_id=rota.id,
        passageiro_id=estudante.id,
        data=dados.data,
        status="reservada",
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    auditoria.log_evento(
        db,
        auditoria.VIAGEM_RESERVADA,
        usuario_id=estudante.id,
        detalhe=f"viagem_id={v.id} rota_id={rota.id}",
    )
    return viagem_to_out(v, db=db)


@router.delete("/viagens/{viagem_id}", status_code=204)
def cancelar_minha_viagem(
    viagem_id: int,
    db: Session = Depends(get_db),
    estudante: Usuario = Depends(get_estudante),
):
    v = (
        db.query(Viagem)
        .filter(Viagem.id == viagem_id, Viagem.passageiro_id == estudante.id)
        .first()
    )
    if not v:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")

    if v.status != "reservada":
        raise HTTPException(
            status_code=400,
            detail="Apenas viagens reservadas podem ser canceladas.",
        )

    v.status = "cancelada"
    db.add(v)
    db.commit()
    auditoria.log_evento(
        db,
        auditoria.VIAGEM_CANCELADA,
        usuario_id=estudante.id,
        detalhe=f"viagem_id={v.id}",
    )


@router.post(
    "/viagens/{viagem_id}/avaliar",
    response_model=AvaliacaoOut,
    status_code=201,
)
def avaliar_viagem(
    viagem_id: int,
    dados: AvaliacaoCreate,
    db: Session = Depends(get_db),
    estudante: Usuario = Depends(get_estudante),
):
    v = (
        db.query(Viagem)
        .filter(Viagem.id == viagem_id, Viagem.passageiro_id == estudante.id)
        .first()
    )
    if not v:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")

    if v.status != "realizada":
        raise HTTPException(
            status_code=400,
            detail="Apenas viagens realizadas podem ser avaliadas.",
        )

    if v.avaliacao is not None:
        raise HTTPException(status_code=400, detail="Viagem já avaliada.")

    av = Avaliacao(
        viagem_id=v.id,
        nota=dados.nota,
        comentario=(dados.comentario or "").strip() or None,
    )
    db.add(av)
    db.commit()
    db.refresh(av)
    auditoria.log_evento(
        db,
        auditoria.AVALIACAO_CRIADA,
        usuario_id=estudante.id,
        detalhe=f"viagem_id={v.id} nota={av.nota}",
    )
    return AvaliacaoOut.model_validate(av)

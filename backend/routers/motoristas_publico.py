from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from avaliacoes_service import media_motorista
from db import get_db
from models import Usuario
from schemas import MotoristaPublicoOut

router = APIRouter(prefix="/api/motoristas", tags=["motoristas"])


@router.get("/{motorista_id}", response_model=MotoristaPublicoOut)
def perfil_publico(motorista_id: int, db: Session = Depends(get_db)):
    user = (
        db.query(Usuario).filter(Usuario.id == motorista_id, Usuario.perfil == "motorista").first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="Motorista não encontrado")

    media, total = media_motorista(db, user.id)
    return MotoristaPublicoOut(
        id=user.id,
        nome=user.nome,
        media_avaliacoes=media,
        total_avaliacoes=total,
    )

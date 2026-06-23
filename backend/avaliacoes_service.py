from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Avaliacao, Rota, Viagem


def media_motorista(db: Session, motorista_id: int) -> tuple[float | None, int]:
    """Retorna (media, total) das avaliações das viagens nas rotas do motorista."""
    row = (
        db.query(func.avg(Avaliacao.nota), func.count(Avaliacao.id))
        .join(Viagem, Avaliacao.viagem_id == Viagem.id)
        .join(Rota, Viagem.rota_id == Rota.id)
        .filter(Rota.motorista_id == motorista_id)
        .one()
    )
    media, total = row
    return (round(float(media), 2) if media is not None else None), int(total or 0)

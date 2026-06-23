from sqlalchemy.orm import Session

from avaliacoes_service import media_motorista
from models import Rota, Viagem
from schemas import MotoristaResumoCard, RotaOut, ViagemOut
from trajeto import duracao_estimada_min, hora_mais_minutos


def rota_to_out(r: Rota, db: Session | None = None) -> RotaOut:
    """Converte Rota → RotaOut. Se db informado, enriquece com média do motorista."""
    motorista_info = None
    if db is not None and r.motorista is not None:
        media, total = media_motorista(db, r.motorista_id)
        motorista_info = MotoristaResumoCard(
            id=r.motorista.id,
            nome=r.motorista.nome,
            media_avaliacoes=media,
            total_avaliacoes=total,
        )

    duracao = duracao_estimada_min(
        r.origem_lat, r.origem_lng, r.destino_lat, r.destino_lng
    )
    chegada = hora_mais_minutos(r.hora_ida, duracao)

    return RotaOut(
        id=r.id,
        motorista_id=r.motorista_id,
        nome=r.nome,
        origem=r.origem,
        destino=r.destino,
        origem_lat=r.origem_lat,
        origem_lng=r.origem_lng,
        destino_lat=r.destino_lat,
        destino_lng=r.destino_lng,
        hora_ida=r.hora_ida,
        hora_volta=r.hora_volta,
        vagas=r.vagas,
        veiculo=r.veiculo,
        dias_semana=r.dias_semana.split(","),
        preco=r.preco,
        motorista=motorista_info,
        duracao_estimada_min=duracao,
        hora_chegada_estimada=chegada,
    )


def viagem_to_out(v: Viagem, db: Session | None = None) -> ViagemOut:
    return ViagemOut(
        id=v.id,
        rota=rota_to_out(v.rota, db=db),
        data=v.data,
        status=v.status,
        passageiro_id=v.passageiro_id,
        avaliada=v.avaliacao is not None,
    )

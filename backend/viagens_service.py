from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import Rota, Viagem

# Map date.weekday() (seg=0..dom=6) → código usado em Rota.dias_semana
_WEEKDAY_TO_KEY = {
    0: "seg",
    1: "ter",
    2: "qua",
    3: "qui",
    4: "sex",
    5: "sab",
    6: "dom",
}


def dia_da_semana_key(d: date) -> str:
    return _WEEKDAY_TO_KEY[d.weekday()]


def rota_atende_data(rota: Rota, d: date) -> bool:
    dias = {x.strip() for x in rota.dias_semana.split(",") if x.strip()}
    return dia_da_semana_key(d) in dias


def vagas_disponiveis(db: Session, rota: Rota, d: date) -> int:
    reservadas = (
        db.query(Viagem)
        .filter(
            Viagem.rota_id == rota.id,
            Viagem.data == d,
            Viagem.status == "reservada",
        )
        .count()
    )
    return rota.vagas - reservadas


def validar_reserva(db: Session, rota: Rota, d: date, passageiro_id: int) -> None:
    if d < date.today():
        raise HTTPException(status_code=400, detail="Data não pode estar no passado.")

    if not rota_atende_data(rota, d):
        raise HTTPException(
            status_code=400,
            detail="Esta rota não opera no dia da semana selecionado.",
        )

    ja_reservada = (
        db.query(Viagem)
        .filter(
            Viagem.rota_id == rota.id,
            Viagem.data == d,
            Viagem.passageiro_id == passageiro_id,
            Viagem.status == "reservada",
        )
        .first()
    )
    if ja_reservada:
        raise HTTPException(
            status_code=400,
            detail="Você já tem uma reserva ativa nesta rota e data.",
        )

    if vagas_disponiveis(db, rota, d) <= 0:
        raise HTTPException(status_code=409, detail="Não há vagas disponíveis.")

from sqlalchemy.orm import Session

from models import EventoAuditoria

# Tipos canônicos — manter limitado e estável p/ facilitar consulta
LOGIN_SUCESSO = "login_sucesso"
LOGIN_FALHA = "login_falha"
REGISTRO = "registro"
LOGOUT = "logout"
ROTA_CRIADA = "rota_criada"
ROTA_ATUALIZADA = "rota_atualizada"
ROTA_DELETADA = "rota_deletada"
VIAGEM_RESERVADA = "viagem_reservada"
VIAGEM_CANCELADA = "viagem_cancelada"
VIAGEM_STATUS_ATUALIZADO = "viagem_status_atualizado"
AVALIACAO_CRIADA = "avaliacao_criada"
USUARIO_ATUALIZADO = "usuario_atualizado"
USUARIO_DELETADO = "usuario_deletado"


def log_evento(
    db: Session,
    tipo: str,
    usuario_id: int | None = None,
    ip: str | None = None,
    detalhe: str | None = None,
) -> None:
    """Registra um evento. Best-effort — falha silenciosa não derruba a request."""
    try:
        ev = EventoAuditoria(
            usuario_id=usuario_id,
            tipo=tipo,
            ip=ip,
            detalhe=(detalhe or "")[:500] or None,
        )
        db.add(ev)
        db.commit()
    except Exception:
        db.rollback()

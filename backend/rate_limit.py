from datetime import UTC, datetime

from fastapi import HTTPException, Request

from config import settings
from redis_client import get_redis

# Fallback in-memory — usado quando Redis está down (degradar > derrubar)
tentativas_falhas: dict[str, list[datetime]] = {}
registros_por_ip: dict[str, list[datetime]] = {}


def _expirar(items: list[datetime], janela_s: int) -> list[datetime]:
    agora = datetime.now(UTC)
    return [t for t in items if (agora - t).total_seconds() < janela_s]


def _incr_e_contar(chave: str, janela_s: int, limite: int) -> int:
    """
    Sliding-window approximado usando contador com TTL.
    Retorna o valor atual depois do incremento. Se ultrapassar `limite`, caller decide.
    Redis ausente → cai no in-memory.
    """
    r = get_redis()
    if r is None:
        return _incr_in_memory(chave, janela_s, limite)

    try:
        pipe = r.pipeline()
        pipe.incr(chave)
        pipe.expire(chave, janela_s)
        valor, _ = pipe.execute()
        return int(valor)
    except Exception:
        return _incr_in_memory(chave, janela_s, limite)


def _incr_in_memory(chave: str, janela_s: int, limite: int) -> int:
    """Fallback. Usa o dict global escolhido por prefixo da chave."""
    bucket = tentativas_falhas if chave.startswith("login:") else registros_por_ip
    atual = _expirar(bucket.get(chave, []), janela_s)
    bucket[chave] = atual
    atual.append(datetime.now(UTC))
    return len(atual)


def _ler_e_checar(chave: str, janela_s: int, limite: int) -> int:
    """Lê valor atual sem incrementar (pra `checar_*` sem registrar)."""
    r = get_redis()
    if r is None:
        bucket = tentativas_falhas if chave.startswith("login:") else registros_por_ip
        atual = _expirar(bucket.get(chave, []), janela_s)
        bucket[chave] = atual
        return len(atual)
    try:
        valor = r.get(chave)
        return int(valor) if valor else 0
    except Exception:
        return 0


def _chave_login(email: str) -> str:
    return f"login:{email}"


def _chave_registro(ip: str) -> str:
    return f"registro:{ip}"


def checar_rate_limit_login(email: str) -> None:
    chave = _chave_login(email)
    atual = _ler_e_checar(chave, settings.janela_tentativas_login_s, settings.max_tentativas_login)
    if atual >= settings.max_tentativas_login:
        raise HTTPException(
            status_code=429,
            detail="Muitas tentativas de login. Aguarde alguns minutos e tente novamente.",
        )


def registrar_falha_login(email: str) -> None:
    _incr_e_contar(
        _chave_login(email),
        settings.janela_tentativas_login_s,
        settings.max_tentativas_login,
    )


def limpar_falhas_login(email: str) -> None:
    r = get_redis()
    chave = _chave_login(email)
    if r is not None:
        try:
            r.delete(chave)
            return
        except Exception:
            pass
    tentativas_falhas.pop(chave, None)


def checar_rate_limit_registro(ip: str) -> None:
    chave = _chave_registro(ip)
    novo = _incr_e_contar(chave, settings.janela_registro_s, settings.max_registros_por_ip)
    if novo > settings.max_registros_por_ip:
        raise HTTPException(
            status_code=429,
            detail="Muitos cadastros recentes desse endereço. Tente novamente mais tarde.",
        )


def get_client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def reset_state() -> None:
    """Para uso em testes — limpa Redis (chaves do rate-limit) e dicts in-memory."""
    tentativas_falhas.clear()
    registros_por_ip.clear()
    r = get_redis()
    if r is not None:
        try:
            for chave in r.scan_iter("login:*"):
                r.delete(chave)
            for chave in r.scan_iter("registro:*"):
                r.delete(chave)
        except Exception:
            pass

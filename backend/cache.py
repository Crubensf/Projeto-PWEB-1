import contextlib
import hashlib
import json
from typing import Any

from redis_client import get_redis


def _hash_chave(params: dict[str, Any]) -> str:
    """Chave estável e curta independente de ordem dos params."""
    blob = json.dumps(params, sort_keys=True, default=str)
    return hashlib.sha1(blob.encode()).hexdigest()[:16]


def cache_get(namespace: str, params: dict[str, Any]) -> Any | None:
    r = get_redis()
    if r is None:
        return None
    chave = f"cache:{namespace}:{_hash_chave(params)}"
    try:
        raw = r.get(chave)
        return json.loads(raw) if raw else None
    except Exception:
        return None


def cache_set(namespace: str, params: dict[str, Any], valor: Any, ttl_s: int) -> None:
    r = get_redis()
    if r is None:
        return
    chave = f"cache:{namespace}:{_hash_chave(params)}"
    with contextlib.suppress(Exception):
        r.set(chave, json.dumps(valor, default=str), ex=ttl_s)


def cache_invalidate(namespace: str) -> None:
    """Apaga todas as chaves do namespace. Usar quando dados mudam."""
    r = get_redis()
    if r is None:
        return
    try:
        for chave in r.scan_iter(f"cache:{namespace}:*"):
            r.delete(chave)
    except Exception:
        pass

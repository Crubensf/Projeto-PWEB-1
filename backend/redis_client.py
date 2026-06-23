from functools import lru_cache
from typing import Optional

import redis

from config import settings


@lru_cache(maxsize=1)
def get_redis() -> Optional["redis.Redis"]:
    """
    Cliente Redis singleton. Retorna None se Redis estiver indisponível —
    callers devem ter fallback (rate-limit é melhor degradar do que derrubar a API).
    """
    try:
        client = redis.Redis.from_url(
            settings.redis_url, decode_responses=True, socket_connect_timeout=2
        )
        client.ping()
        return client
    except Exception:
        return None


def reset_redis_singleton() -> None:
    """Para testes: força recriar o cliente na próxima chamada."""
    get_redis.cache_clear()

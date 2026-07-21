import json
import logging
from typing import Any

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: redis.Redis | None = None
_redis_available: bool | None = None


def get_redis() -> redis.Redis | None:
    global _redis_client, _redis_available
    if _redis_available is False:
        return None
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
            _redis_client.ping()
            _redis_available = True
        except redis.RedisError:
            logger.warning("Redis unavailable, running without cache")
            _redis_available = False
            return None
    return _redis_client


def cache_get(key: str) -> dict[str, Any] | None:
    client = get_redis()
    if not client:
        return None
    try:
        data = client.get(key)
        if data:
            return json.loads(data)
    except redis.RedisError:
        pass
    return None


def cache_set(key: str, value: dict[str, Any], ttl: int = 86400) -> None:
    client = get_redis()
    if not client:
        return
    try:
        client.setex(key, ttl, json.dumps(value, default=str))
    except redis.RedisError:
        pass

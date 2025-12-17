"""Redis cache management."""

import json
from typing import Any

from redis.asyncio import Redis

from app.config import get_settings

settings = get_settings()


class CacheManager:
    """Redis cache manager."""

    def __init__(self) -> None:
        """Initialize cache manager."""
        self.redis: Redis | None = None

    async def connect(self) -> None:
        """Connect to Redis."""
        self.redis = await Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.REDIS_POOL_SIZE,
        )

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        if not self.redis:
            return None
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: int | None = None,
    ) -> bool:
        """Set value in cache."""
        if not self.redis:
            return False
        serialized = json.dumps(value)
        result = await self.redis.set(key, serialized, ex=expire)
        return bool(result) if result is not None else False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis:
            return False
        result = await self.redis.delete(key)
        return bool(result > 0)

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.redis:
            return False
        result = await self.redis.exists(key)
        return bool(result) if result is not None else False


cache_manager = CacheManager()


async def get_cache() -> CacheManager:
    """Get cache manager instance."""
    return cache_manager

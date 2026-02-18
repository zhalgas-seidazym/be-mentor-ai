from __future__ import annotations

import inspect
from typing import Optional

import redis.asyncio as redis


class RedisConnection:
    def __init__(
            self,
            host: str = "localhost",
            port: int = 6379,
            db: int = 0,
            url: Optional[str] = None,
            decode_responses: bool = True,
    ):
        self.url = url or f"redis://{host}:{port}/{db}"
        self.decode_responses = decode_responses
        self._client: Optional[redis.Redis] = None

    async def connect(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.Redis.from_url(
                self.url,
                encoding="utf-8",
                decode_responses=self.decode_responses,
            )
            await self._client.ping()
        return self._client

    async def disconnect(self) -> None:
        if not self._client:
            return

        close = getattr(self._client, "aclose", None) or getattr(self._client, "close", None)
        if close:
            if inspect.iscoroutinefunction(close):
                await close()
            else:
                close()

        pool = getattr(self._client, "connection_pool", None)
        if pool and hasattr(pool, "disconnect"):
            if inspect.iscoroutinefunction(pool.disconnect):
                await pool.disconnect()
            else:
                pool.disconnect()

        self._client = None

    async def __aenter__(self) -> redis.Redis:
        return await self.connect()

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.disconnect()
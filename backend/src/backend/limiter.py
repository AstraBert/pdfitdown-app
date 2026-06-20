import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi.applications import FastAPI
from fastapi_limiter import FastAPILimiter
from redis.asyncio import Redis


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    redis_connection = Redis.from_url(url=os.getenv("REDIS_URI", ""))
    await FastAPILimiter.init(redis_connection)
    yield
    await FastAPILimiter.close()

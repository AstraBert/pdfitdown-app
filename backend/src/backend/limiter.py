import os
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi.applications import FastAPI
from fastapi_limiter import FastAPILimiter


@asynccontextmanager
async def lifespan(_: FastAPI):
    redis_connection = redis.Redis.from_url(url=os.getenv("REDIS_URI", ""))
    await FastAPILimiter.init(redis_connection)
    yield
    await FastAPILimiter.close()

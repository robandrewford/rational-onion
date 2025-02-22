# rational_onion/services/caching_service.py

import aioredis
from fastapi import HTTPException
from rational_onion.config import get_settings

settings = get_settings()

redis = aioredis.from_url(
    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
    password=settings.REDIS_PASSWORD,
    db=settings.REDIS_DB,
    ssl=settings.REDIS_SSL,
    encoding="utf-8",
    decode_responses=True
)

caching_enabled = settings.CACHE_ENABLED

async def toggle_cache(enable: bool):
    global caching_enabled
    caching_enabled = enable
    return {"message": f"Caching {'enabled' if enable else 'disabled'}."}
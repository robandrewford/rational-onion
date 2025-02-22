# rational_onion/services/caching_service.py

import aioredis
from fastapi import HTTPException

caching_enabled = False
redis = None

async def init_redis():
    global redis
    try:
        redis = await aioredis.from_url("redis://localhost")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis initialization failed: {e}")

async def toggle_cache(enable: bool):
    global caching_enabled
    caching_enabled = enable
    return {"message": f"Caching {'enabled' if enable else 'disabled'}."}
from fastapi import HTTPException, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from typing import AsyncGenerator
from rational_onion.config import get_settings

settings = get_settings()

# Initialize rate limiter with default in-memory storage
limiter = Limiter(key_func=get_remote_address)

def handle_rate_limit_exceeded(request: Request, exc: RateLimitExceeded) -> HTTPException:
    """Handler for rate limit exceeded errors"""
    return HTTPException(
        status_code=429,
        detail={
            "error_type": "RATE_LIMIT_EXCEEDED",
            "message": "Rate limit exceeded",
            "details": {
                "limit": str(exc.limit),
                "reset_at": str(exc.reset_at)
            }
        }
    )

async def get_db_driver() -> AsyncGenerator[AsyncDriver, None]:
    """Get Neo4j database driver"""
    driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        database=settings.NEO4J_DATABASE,
        max_connection_pool_size=settings.NEO4J_MAX_CONNECTION_POOL_SIZE,
        connection_timeout=settings.NEO4J_CONNECTION_TIMEOUT,
        encrypted=settings.NEO4J_ENCRYPTION_ENABLED
    )
    try:
        yield driver
    finally:
        await driver.close()

async def get_db(driver: AsyncDriver = Depends(get_db_driver)) -> AsyncGenerator[AsyncSession, None]:
    """Get Neo4j database session"""
    async with driver.session() as session:
        try:
            yield session
        finally:
            await session.close() 
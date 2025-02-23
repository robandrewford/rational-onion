from fastapi import HTTPException, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import ServiceUnavailable, DatabaseError as Neo4jDatabaseError
from typing import AsyncGenerator, AsyncIterator
from rational_onion.config import get_settings
from rational_onion.api.errors import ErrorType, BaseAPIError, DatabaseError

settings = get_settings()

# Initialize rate limiter with default in-memory storage
limiter = Limiter(key_func=get_remote_address)

async def get_db_driver() -> AsyncIterator[AsyncDriver]:
    """Get Neo4j database driver"""
    try:
        driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            database=settings.NEO4J_DATABASE,
            max_connection_pool_size=settings.NEO4J_MAX_CONNECTION_POOL_SIZE,
            connection_timeout=settings.NEO4J_CONNECTION_TIMEOUT,
            encrypted=settings.NEO4J_ENCRYPTION_ENABLED
        )
        # Verify connection
        try:
            await driver.verify_connectivity()
        except Exception as e:
            raise BaseAPIError(
                error_type=ErrorType.DATABASE_ERROR,
                message="Failed to connect to database",
                status_code=500,
                details={"error": str(e)}
            )
        yield driver
    except Exception as e:
        raise BaseAPIError(
            error_type=ErrorType.DATABASE_ERROR,
            message="Failed to create database driver",
            status_code=500,
            details={"error": str(e)}
        )
    finally:
        if 'driver' in locals():
            await driver.close()

async def get_db(driver: AsyncDriver = Depends(get_db_driver)) -> AsyncIterator[AsyncSession]:
    """Get Neo4j database session"""
    try:
        async with driver.session() as session:
            try:
                # Test query to verify session
                result = await session.run("RETURN 1 as test")
                await result.consume()
                yield session
            except (ServiceUnavailable, Neo4jDatabaseError) as e:
                raise BaseAPIError(
                    error_type=ErrorType.DATABASE_ERROR,
                    message="Database session error",
                    status_code=500,
                    details={"error": str(e)}
                )
    except Exception as e:
        raise BaseAPIError(
            error_type=ErrorType.DATABASE_ERROR,
            message="Failed to create database session",
            status_code=500,
            details={"error": str(e)}
        ) 
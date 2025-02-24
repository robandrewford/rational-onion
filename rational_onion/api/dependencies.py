from fastapi import HTTPException, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from neo4j import AsyncGraphDatabase, AsyncSession
from neo4j.exceptions import ServiceUnavailable, DatabaseError as Neo4jDatabaseError
from typing import AsyncGenerator
from rational_onion.config import get_settings, get_test_settings
from rational_onion.api.errors import ErrorType, BaseAPIError, DatabaseError
import sys

settings = get_test_settings() if "pytest" in sys.modules else get_settings()

# Initialize rate limiter with default in-memory storage
limiter = Limiter(key_func=get_remote_address)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get Neo4j database session"""
    driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        max_connection_lifetime=60,
        max_connection_pool_size=1,
        connection_timeout=5,
        encrypted=False
    )
    
    try:
        await driver.verify_connectivity()
        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            yield session
    except (ServiceUnavailable, Neo4jDatabaseError) as e:
        # Only catch actual database errors
        raise DatabaseError(f"Failed to connect to database: {str(e)}")
    except Exception as e:
        # Re-raise other exceptions
        raise e
    finally:
        await driver.close()

async def verify_api_key(request: Request) -> str:
    """Verify that the provided API key is valid"""
    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key not in settings.VALID_API_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return api_key 
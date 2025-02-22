import pytest
from fastapi.testclient import TestClient
from neo4j import AsyncGraphDatabase, AsyncSession, AsyncDriver
import aioredis
from rational_onion.api.main import app
from rational_onion.config import get_test_settings
from typing import Dict, Any, AsyncGenerator

settings = get_test_settings()

@pytest.fixture
def test_client() -> TestClient:
    """Create a test client instance"""
    return TestClient(app)

@pytest.fixture
def valid_api_key() -> str:
    """Provide valid API key for tests"""
    return settings.VALID_API_KEYS[0]

@pytest.fixture
async def neo4j_test_driver() -> AsyncGenerator[AsyncDriver, None]:
    """Create a test Neo4j driver instance"""
    driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        database=settings.NEO4J_DATABASE
    )
    try:
        yield driver
    finally:
        await driver.close()

@pytest.fixture
async def neo4j_test_session(neo4j_test_driver: AsyncDriver) -> AsyncGenerator[AsyncSession, None]:
    """Create a test Neo4j session"""
    async with neo4j_test_driver.session() as session:
        try:
            yield session
        finally:
            await session.close()

@pytest.fixture
async def redis_test_client() -> AsyncGenerator[aioredis.Redis, None]:
    """Create and yield Redis test client"""
    redis = await aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        encoding="utf-8",
        decode_responses=True
    )
    yield redis
    await redis.close()

@pytest.fixture
def sample_argument_data() -> Dict[str, str]:
    """Provide sample argument data for tests"""
    return settings.DEFAULT_TEST_ARGUMENT 
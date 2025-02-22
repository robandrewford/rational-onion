import pytest
from fastapi.testclient import TestClient
from neo4j import AsyncGraphDatabase
import aioredis
from rational_onion.api.main import app
from rational_onion.config import get_test_settings

@pytest.fixture
def test_client():
    """Create a test client instance"""
    return TestClient(app)

@pytest.fixture
def valid_api_key():
    """Provide a valid API key for testing"""
    return "test_api_key_123"

@pytest.fixture
async def neo4j_test_driver():
    """Create a test Neo4j driver instance"""
    settings = get_test_settings()
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password)
    )
    yield driver
    await driver.close()

@pytest.fixture
async def redis_test_client():
    """Create and yield Redis test client"""
    redis = await aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        encoding="utf-8",
        decode_responses=True
    )
    yield redis
    await redis.close()

@pytest.fixture
def sample_argument_data():
    """Provide sample argument data for tests"""
    return settings.DEFAULT_TEST_ARGUMENT 
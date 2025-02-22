import pytest
from fastapi.testclient import TestClient
from neo4j import AsyncGraphDatabase
import aioredis
from rational_onion.api.main import app
from rational_onion.services.neo4j_service import driver as neo4j_driver
from rational_onion.services.caching_service import redis

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
async def neo4j_test_driver():
    test_uri = "bolt://localhost:7687"
    test_auth = ("neo4j", "test_password")
    driver = AsyncGraphDatabase.driver(test_uri, auth=test_auth)
    yield driver
    await driver.close()

@pytest.fixture
async def redis_test_client():
    redis = await aioredis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)
    yield redis
    await redis.close()

@pytest.fixture
def valid_api_key():
    return "abc123"

@pytest.fixture
async def sample_argument_data():
    return {
        "claim": "AI regulation is necessary",
        "grounds": "Unregulated AI development poses risks",
        "warrant": "Risk mitigation requires oversight",
        "rebuttal": "Some regulation might stifle innovation"
    } 
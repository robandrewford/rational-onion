# tests/test_api.py

import pytest
from fastapi.testclient import TestClient
from rational_onion.api.main import app
from rational_onion.config import get_test_settings

settings = get_test_settings()

# Remove global client initialization
# client = TestClient(app)

def test_insert_argument(test_client, valid_api_key, sample_argument_data):
    response = test_client.post(
        "/insert-argument",
        headers={"X-API-Key": valid_api_key},
        json=sample_argument_data
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Argument successfully inserted."

def test_api_health(test_client, valid_api_key):
    """Test API health endpoint"""
    response = test_client.get(
        "/health",
        headers={"X-API-Key": valid_api_key}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_api_rate_limiting(test_client, valid_api_key):
    """Test API rate limiting"""
    rate_limit = int(settings.RATE_LIMIT.split('/')[0])
    responses = []
    
    # Make requests up to rate limit
    for _ in range(rate_limit + 1):
        response = test_client.get(
            "/api/arguments",
            headers={"X-API-Key": valid_api_key}
        )
        responses.append(response)
    
    # Verify rate limiting
    assert any(r.status_code == 429 for r in responses)

@pytest.mark.asyncio
async def test_api_database_connection(neo4j_test_driver, valid_api_key):
    """Test database connectivity"""
    async with neo4j_test_driver.session() as session:
        result = await session.run("RETURN 1 as n")
        record = await result.single()
        assert record["n"] == 1

# ... rest of tests using test_client fixture
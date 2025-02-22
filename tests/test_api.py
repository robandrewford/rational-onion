# tests/test_api.py

import pytest
from fastapi.testclient import TestClient
from rational_onion.api.main import app
from rational_onion.config import get_test_settings, get_settings
from typing import Dict, Any

settings = get_test_settings()

# Remove global client initialization
# client = TestClient(app)

def test_insert_argument_success(test_client: TestClient, valid_api_key: str) -> None:
    """Test successful argument insertion"""
    response = test_client.post(
        "/insert-argument",
        headers={"X-API-Key": valid_api_key},
        json={
            "claim": "Test claim",
            "grounds": "Test grounds",
            "warrant": "Test warrant"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "argument_id" in data
    assert isinstance(data["argument_id"], int)

def test_insert_argument_validation_error(test_client: TestClient, valid_api_key: str) -> None:
    """Test argument insertion with validation error"""
    response = test_client.post(
        "/insert-argument",
        headers={"X-API-Key": valid_api_key},
        json={
            "claim": "c" * (settings.MAX_CLAIM_LENGTH + 1),
            "grounds": "Test grounds",
            "warrant": "Test warrant"
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error_type"] == "VALIDATION_ERROR"
    assert data["detail"]["field"] == "claim"

def test_verify_argument_structure_success(test_client: TestClient, valid_api_key: str) -> None:
    """Test successful argument structure verification"""
    # First insert an argument
    insert_response = test_client.post(
        "/insert-argument",
        headers={"X-API-Key": valid_api_key},
        json={
            "claim": "Test claim",
            "grounds": "Test grounds",
            "warrant": "Test warrant"
        }
    )
    assert insert_response.status_code == 200
    argument_id = insert_response.json()["argument_id"]

    # Then verify its structure
    response = test_client.post(
        "/verify-argument-structure",
        headers={"X-API-Key": valid_api_key},
        json={"id": argument_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

def test_rate_limit_exceeded(test_client: TestClient, valid_api_key: str) -> None:
    """Test rate limiting"""
    # Make multiple requests to exceed rate limit
    for _ in range(11):  # Rate limit is 10/minute
        test_client.post(
            "/insert-argument",
            headers={"X-API-Key": valid_api_key},
            json={
                "claim": "Test claim",
                "grounds": "Test grounds",
                "warrant": "Test warrant"
            }
        )
    
    # The 11th request should fail
    response = test_client.post(
        "/insert-argument",
        headers={"X-API-Key": valid_api_key},
        json={
            "claim": "Test claim",
            "grounds": "Test grounds",
            "warrant": "Test warrant"
        }
    )
    assert response.status_code == 429
    data = response.json()
    assert data["detail"]["error_type"] == "RATE_LIMIT_EXCEEDED"
    assert "limit" in data["detail"]["details"]
    assert "reset_at" in data["detail"]["details"]

@pytest.mark.asyncio
async def test_api_database_connection(neo4j_test_session: Any, valid_api_key: str) -> None:
    """Test database connectivity"""
    result = await neo4j_test_session.run("RETURN 1 as n")
    record = await result.single()
    assert record["n"] == 1

# ... rest of tests using test_client fixture
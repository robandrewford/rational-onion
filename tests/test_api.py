# tests/test_api.py

import pytest
from fastapi.testclient import TestClient
from rational_onion.api.main import app
from rational_onion.config import get_test_settings, get_settings
from typing import Dict, Any
from fastapi import Request

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
    assert "argument_id" in data
    assert isinstance(data["argument_id"], str)
    assert "message" in data
    assert data["message"] == "Argument created successfully"

def test_insert_argument_validation_error(test_client: TestClient, valid_api_key: str) -> None:
    """Test validation error handling for argument insertion"""
    response = test_client.post(
        "/insert-argument",
        headers={"X-API-Key": valid_api_key},
        json={
            # Missing required fields
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert data["detail"]["error_type"] == "VALIDATION_ERROR"

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
        json={"argument_id": argument_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["is_valid"] == True
    assert data["has_cycles"] == False
    assert isinstance(data["orphaned_nodes"], list)

def test_rate_limit_exceeded(test_client: TestClient, valid_api_key: str) -> None:
    """Test that the rate limit exceeded handler returns the expected response format."""
    # Import the necessary components
    from rational_onion.api.rate_limiting import rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.wrappers import Limit
    from limits.strategies import FixedWindowRateLimiter
    from limits.storage import MemoryStorage
    from limits import RateLimitItem
    
    # Create a simple mock request
    mock_request = Request({"type": "http", "method": "POST", "path": "/insert-argument"})
    
    # Create a RateLimitItem
    rate_limit_item = RateLimitItem(100, 1, "LIMITER")
    
    # Create a proper Limit object
    limit = Limit(
        limit=rate_limit_item,
        key_func=lambda: "test_key",
        scope="test_scope",
        per_method=True,
        methods=["POST"],
        error_message="Rate limit exceeded",
        exempt_when=lambda: False,
        cost=1,
        override_defaults=False
    )
    
    # Create a RateLimitExceeded exception with the Limit object
    exc = RateLimitExceeded(limit)
    
    # Call the handler directly
    response = rate_limit_exceeded_handler(mock_request, exc)
    
    # Verify the response
    assert response.status_code == 429
    data = response.body.decode()
    import json
    data = json.loads(data)
    assert data["detail"]["error_type"] == "RATE_LIMIT_ERROR"
    assert data["detail"]["message"] == "Rate limit exceeded"

@pytest.mark.asyncio
async def test_api_database_connection(neo4j_test_session: Any, valid_api_key: str) -> None:
    """Test database connectivity"""
    result = await neo4j_test_session.run("RETURN 1 as n")
    record = await result.single()
    assert record["n"] == 1

# ... rest of tests using test_client fixture
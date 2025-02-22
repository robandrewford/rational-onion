# tests/test_verification.py

import pytest
from fastapi.testclient import TestClient
from rational_onion.api.main import app
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import Dict
from neo4j import AsyncGraphDatabase
import aioredis

client = TestClient(app)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/arguments")
@limiter.limit("5/minute")
async def get_arguments():
    return {"message": "Rate limited endpoint"}

def test_verify_argument_structure(test_client, valid_api_key):
    """Tests the structural verification endpoint."""
    response = test_client.get(
        "/verify-argument-structure", 
        headers={"X-API-Key": valid_api_key}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert_valid_verification_response(data)

@pytest.mark.asyncio
async def test_verify_argument_structure_with_cycles(test_client, neo4j_test_driver, valid_api_key):
    """Tests cycle detection in argument structure."""
    # Setup: Create a cyclic structure
    async with neo4j_test_driver.session() as session:
        await session.run("""
            CREATE (c1:Claim {text: 'Claim 1'})
            CREATE (c2:Claim {text: 'Claim 2'})
            CREATE (c1)-[:SUPPORTS]->(c2)
            CREATE (c2)-[:SUPPORTS]->(c1)
        """)

    response = test_client.get(
        "/verify-argument-structure",
        headers={"X-API-Key": valid_api_key}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["has_cycles"] == True

@pytest.mark.asyncio
async def test_verify_argument_structure_with_orphans(test_client, neo4j_test_driver, valid_api_key):
    """Tests orphaned node detection."""
    # Setup: Create an orphaned node
    async with neo4j_test_driver.session() as session:
        await session.run("""
            CREATE (c:Claim {text: 'Orphaned Claim'})
        """)

    response = test_client.get(
        "/verify-argument-structure",
        headers={"X-API-Key": valid_api_key}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["orphaned_nodes"]) > 0

def assert_valid_verification_response(data):
    """Helper function to validate verification response structure."""
    assert "has_cycles" in data
    assert "orphaned_nodes" in data
    assert "message" in data
    assert isinstance(data["has_cycles"], bool)
    assert isinstance(data["orphaned_nodes"], list)
    assert isinstance(data["message"], str)

@pytest.mark.asyncio
async def test_verification_error_handling(test_client, neo4j_test_driver, valid_api_key):
    """Tests error handling in verification endpoint."""
    # Force an error by closing the database connection
    await neo4j_test_driver.close()
    
    response = test_client.get(
        "/verify-argument-structure",
        headers={"X-API-Key": valid_api_key}
    )
    assert response.status_code == 500
    assert "detail" in response.json()

@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {
        "status": "healthy",
        "neo4j": await check_neo4j_connection(),
        "redis": await check_redis_connection(),
        "api_version": "2.0"
    }
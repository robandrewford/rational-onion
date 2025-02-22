# tests/test_verification.py

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import Dict, List, Optional, Any
from neo4j import AsyncGraphDatabase
import asyncio
from rational_onion.api.main import app
from rational_onion.models.toulmin_model import ArgumentResponse
from rational_onion.config import get_test_settings
from rational_onion.api.errors import (
    ArgumentError,
    DatabaseError,
    ValidationError,
    GraphError,
    ErrorType
)
import time

# Remove the global client
# client = TestClient(app)

# Create a fixture in conftest.py instead

TEST_CONSTANTS = {
    "VALID_RELATIONSHIPS": ["SUPPORTS", "JUSTIFIES", "CHALLENGES", "STRENGTHENS"],
    "TIMEOUT_SECONDS": 2.0,
    "MAX_NODES": 100,
    "CONCURRENT_REQUESTS": 5
}

def test_verify_argument_structure(
    test_client: TestClient,
    valid_api_key: str
) -> None:
    """Tests the structural verification endpoint."""
    response = test_client.get(
        "/verify-argument-structure", 
        headers={"X-API-Key": valid_api_key}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert_valid_verification_response(data)

@pytest.mark.asyncio
async def test_verify_argument_structure_with_cycles(
    test_client: TestClient,
    neo4j_test_driver: AsyncGraphDatabase,
    valid_api_key: str
) -> None:
    """Tests cycle detection in argument structure."""
    # Setup: Create a cyclic structure
    async with neo4j_test_driver.session() as session:
        await session.run("""
            CREATE (c1:Claim {text: 'Claim 1'})
            CREATE (c2:Claim {text: 'Claim 2'})
            CREATE (c1)-[:SUPPORTS]->(c2)
            CREATE (c2)-[:SUPPORTS]->(c1)
        """)

@pytest.mark.asyncio
async def test_verify_argument_structure_with_orphans(
    test_client: TestClient,
    neo4j_test_driver: AsyncGraphDatabase,
    valid_api_key: str
) -> None:
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

def assert_valid_verification_response(data: Dict[str, Any]) -> None:
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
    await neo4j_test_driver.aclose()  # Use aclose instead of close
    
    response = test_client.get(
        "/verify-argument-structure",
        headers={"X-API-Key": valid_api_key}
    )
    assert response.status_code == 500
    assert "detail" in response.json()

settings = get_test_settings()

class TestVerification:
    """Test suite for argument verification functionality"""

    @pytest.fixture(autouse=True)
    async def setup_test_data(self, neo4j_test_driver):
        """Setup test data before each test and cleanup after"""
        async with neo4j_test_driver.session() as session:
            # Clear existing data
            await session.run("MATCH (n) DETACH DELETE n")
            
        yield
        
        # Cleanup after test
        async with neo4j_test_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")

    async def create_test_argument(
        self, 
        neo4j_test_driver: AsyncGraphDatabase, 
        argument_data: Optional[Dict[str, str]] = None
    ) -> None:
        """Helper to create test argument in database"""
        argument_data = argument_data or settings.DEFAULT_TEST_ARGUMENT
        async with neo4j_test_driver.session() as session:
            await session.run("""
                CREATE (c:Claim {text: $claim})
                CREATE (g:Grounds {text: $grounds})
                CREATE (w:Warrant {text: $warrant})
                CREATE (g)-[:SUPPORTS]->(c)
                CREATE (w)-[:JUSTIFIES]->(c)
                """,
                claim=argument_data["claim"],
                grounds=argument_data["grounds"],
                warrant=argument_data["warrant"]
            )

    @pytest.mark.asyncio
    async def test_verify_argument_structure(
        self, 
        test_client: TestClient, 
        neo4j_test_driver: AsyncGraphDatabase, 
        valid_api_key: str
    ) -> None:
        """
        Tests the structural verification endpoint.
        
        Args:
            test_client: FastAPI test client
            neo4j_test_driver: Neo4j database driver
            valid_api_key: Valid API key for authentication
            
        Verifies:
            - Endpoint returns 200 status code
            - Response contains expected verification fields
            - Response structure matches expected format
        """
        response = test_client.get(
            "/verify-argument-structure", 
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert_valid_verification_response(data)

    @pytest.mark.asyncio
    async def test_verify_cyclic_structure(
        self,
        test_client: TestClient,
        neo4j_test_driver: AsyncGraphDatabase,
        valid_api_key: str
    ) -> None:
        """Test detection of cyclic arguments"""
        async with neo4j_test_driver.session() as session:
            # Create cyclic structure
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
        assert data["has_cycles"] is True
        assert "Cyclic dependency detected" in data["message"]

    @pytest.mark.asyncio
    async def test_verify_orphaned_nodes(
        self,
        test_client: TestClient,
        neo4j_test_driver: AsyncGraphDatabase,
        valid_api_key: str
    ) -> None:
        """Test detection of orphaned nodes"""
        async with neo4j_test_driver.session() as session:
            # Create orphaned nodes
            await session.run("""
                CREATE (c1:Claim {text: 'Connected Claim'})
                CREATE (g1:Grounds {text: 'Connected Grounds'})
                CREATE (g1)-[:SUPPORTS]->(c1)
                CREATE (c2:Claim {text: 'Orphaned Claim'})
                CREATE (w2:Warrant {text: 'Orphaned Warrant'})
            """)

        response = test_client.get(
            "/verify-argument-structure",
            headers={"X-API-Key": valid_api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["orphaned_nodes"]) == 2
        assert any("Orphaned Claim" in node for node in data["orphaned_nodes"])
        assert any("Orphaned Warrant" in node for node in data["orphaned_nodes"])

    @pytest.mark.asyncio
    async def test_verify_complex_structure(
        self,
        test_client: TestClient,
        neo4j_test_driver: AsyncGraphDatabase,
        valid_api_key: str
    ) -> None:
        """Test verification of complex argument structure"""
        async with neo4j_test_driver.session() as session:
            await session.run("""
                CREATE (c1:Claim {text: 'Main Claim'})
                CREATE (g1:Grounds {text: 'Primary Grounds'})
                CREATE (w1:Warrant {text: 'Primary Warrant'})
                CREATE (r1:Rebuttal {text: 'Rebuttal'})
                CREATE (g2:Grounds {text: 'Supporting Grounds'})
                CREATE (g1)-[:SUPPORTS]->(c1)
                CREATE (w1)-[:JUSTIFIES]->(c1)
                CREATE (r1)-[:CHALLENGES]->(c1)
                CREATE (g2)-[:SUPPORTS]->(g1)
            """)

        response = test_client.get(
            "/verify-argument-structure",
            headers={"X-API-Key": valid_api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert not data["has_cycles"]
        assert len(data["orphaned_nodes"]) == 0

    @pytest.mark.asyncio
    async def test_database_error_handling(
        self,
        test_client: TestClient,
        neo4j_test_driver: AsyncGraphDatabase,
        valid_api_key: str
    ) -> None:
        """Test database error handling"""
        # Force database error by closing connection
        await neo4j_test_driver.close()
        
        response = test_client.get(
            "/verify-argument-structure",
            headers={"X-API-Key": valid_api_key}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert data["error_type"] == ErrorType.DATABASE_ERROR.value
        assert "operation" in data["details"]
        assert "message" in data

    @pytest.mark.asyncio
    @pytest.mark.parametrize("invalid_relation", [
        "UNKNOWN_RELATION",
        "INVALID_TYPE",
        "WRONG_CONNECTION"
    ])
    async def test_invalid_relationship_types(
        self,
        test_client: TestClient,
        neo4j_test_driver: AsyncGraphDatabase,
        valid_api_key: str,
        invalid_relation: str
    ) -> None:
        """Test handling of various invalid relationship types"""
        async with neo4j_test_driver.session() as session:
            await session.run(f"""
                CREATE (c1:Claim {{text: 'Test Claim'}})
                CREATE (c2:Claim {{text: 'Another Claim'}})
                CREATE (c1)-[:{invalid_relation}]->(c2)
            """)
        
        response = test_client.get(
            "/verify-argument-structure",
            headers={"X-API-Key": valid_api_key}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["error_type"] == ErrorType.GRAPH_ERROR.value
        assert f"Invalid relation type: {invalid_relation}" in data["message"]

    def test_validation_error_handling(
        self,
        test_client: TestClient,
        valid_api_key: str
    ) -> None:
        """Test validation error handling"""
        response = test_client.post(
            "/insert-argument",
            headers={"X-API-Key": valid_api_key},
            json={"invalid": "data"}  # Missing required fields
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["error_type"] == ErrorType.VALIDATION_ERROR.value
        assert "details" in data

    def assert_error_response(
        self, 
        data: Dict[str, Any], 
        expected_type: ErrorType
    ) -> None:
        """Helper to validate error response structure"""
        assert "error_type" in data
        assert "message" in data
        assert "details" in data
        assert data["error_type"] == expected_type.value
        assert isinstance(data["message"], str)
        assert isinstance(data["details"], dict)

    @pytest.mark.asyncio
    async def test_verify_mixed_relationship_types(
        self,
        test_client: TestClient,
        neo4j_test_driver: AsyncGraphDatabase,
        valid_api_key: str
    ) -> None:
        """Test verification of arguments with multiple relationship types"""
        async with neo4j_test_driver.session() as session:
            await session.run("""
                CREATE (c1:Claim {text: 'Main Claim'})
                CREATE (g1:Grounds {text: 'Supporting Evidence'})
                CREATE (w1:Warrant {text: 'Logical Connection'})
                CREATE (b1:Backing {text: 'Additional Support'})
                CREATE (g1)-[:SUPPORTS]->(c1)
                CREATE (w1)-[:JUSTIFIES]->(c1)
                CREATE (b1)-[:STRENGTHENS]->(w1)
            """)
        
        response = test_client.get(
            "/verify-argument-structure",
            headers={"X-API-Key": valid_api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert not data["has_cycles"]
        assert len(data["orphaned_nodes"]) == 0
        assert "valid_relationships" in data

    @pytest.mark.asyncio
    async def test_rate_limit_verification_endpoint(
        self,
        test_client: TestClient,
        valid_api_key: str
    ) -> None:
        """Test rate limiting on verification endpoint"""
        responses = []
        rate_limit = int(settings.RATE_LIMIT.split('/')[0])
        
        for _ in range(rate_limit + 1):
            response = test_client.get(
                "/verify-argument-structure",
                headers={"X-API-Key": valid_api_key}
            )
            responses.append(response)
            await asyncio.sleep(0.1)  # Prevent overwhelming the server
        
        assert any(r.status_code == 429 for r in responses)
        assert any("Rate limit exceeded" in r.json()["detail"] for r in responses)

    @pytest.mark.asyncio
    async def test_verify_empty_database(
        self,
        test_client: TestClient,
        neo4j_test_driver: AsyncGraphDatabase,
        valid_api_key: str
    ) -> None:
        """Test verification behavior with empty database"""
        response = test_client.get(
            "/verify-argument-structure",
            headers={"X-API-Key": valid_api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert not data["has_cycles"]
        assert len(data["orphaned_nodes"]) == 0
        assert "No arguments found in database" in data["message"]

    @pytest.mark.asyncio
    async def test_concurrent_verification_access(
        self,
        test_client: TestClient,
        neo4j_test_driver: AsyncGraphDatabase,
        valid_api_key: str
    ) -> None:
        """Test concurrent access to verification endpoint"""
        async def make_request():
            return test_client.get(
                "/verify-argument-structure",
                headers={"X-API-Key": valid_api_key}
            )
        
        # Make multiple concurrent requests
        tasks = [make_request() for _ in range(5)]
        responses = await asyncio.gather(*tasks)
        
        # Verify all requests succeeded
        assert all(r.status_code == 200 for r in responses)
        # Verify consistent responses
        data = [r.json() for r in responses]
        assert len(set(str(d) for d in data)) == 1  # All responses should be identical

    @pytest.mark.asyncio
    async def test_large_argument_structure_performance(
        self,
        test_client: TestClient,
        neo4j_test_driver: AsyncGraphDatabase,
        valid_api_key: str
    ) -> None:
        """Test verification performance with large argument structure"""
        async with neo4j_test_driver.session() as session:
            # Create a large argument structure
            await session.run("""
                UNWIND range(1, 100) as i
                CREATE (c:Claim {text: 'Claim ' + toString(i)})
                WITH collect(c) as claims
                UNWIND range(0, size(claims)-2) as i
                WITH claims[i] as c1, claims[i+1] as c2
                CREATE (c1)-[:SUPPORTS]->(c2)
            """)
        
        start_time = time.time()
        response = test_client.get(
            "/verify-argument-structure",
            headers={"X-API-Key": valid_api_key}
        )
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed_time < 2.0  # Should complete within 2 seconds
        data = response.json()
        assert not data["has_cycles"]
# tests/test_verification.py
import pytest
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator, Union, TypedDict
from fastapi.testclient import TestClient
from neo4j import AsyncDriver, AsyncSession

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

settings = get_test_settings()

class TestConstants(TypedDict):
    VALID_RELATIONSHIPS: List[str]
    TIMEOUT_SECONDS: float
    MAX_NODES: int
    CONCURRENT_REQUESTS: int

TEST_CONSTANTS = TestConstants(
    VALID_RELATIONSHIPS=["SUPPORTS", "JUSTIFIES", "CHALLENGES"],
    TIMEOUT_SECONDS=2.0,
    MAX_NODES=100,
    CONCURRENT_REQUESTS=5
)

def assert_valid_verification_response(data: Dict[str, Any]) -> None:
    """Helper to validate verification response structure"""
    assert "has_cycles" in data
    assert isinstance(data["has_cycles"], bool)
    assert "message" in data
    assert isinstance(data["message"], str)
    assert "status" in data
    assert data["status"] == "success"

@pytest.mark.asyncio
async def test_verification_error_handling(
    test_client: TestClient,
    neo4j_test_driver: AsyncDriver,
    valid_api_key: str
) -> None:
    """Tests error handling in verification endpoint."""
    # Close the driver to force a connection error
    await neo4j_test_driver.close()
    
    response = test_client.get(
        "/verify-argument-structure",
        headers={"X-API-Key": valid_api_key}
    )
    assert response.status_code == 500
    data = response.json()
    assert data["detail"]["error_type"] == "DATABASE_ERROR"
    assert "message" in data["detail"]

class TestVerification:
    """Test verification endpoint functionality"""

    @pytest.fixture(autouse=True)
    async def setup_test_data(self, neo4j_test_session: AsyncSession) -> AsyncGenerator[None, None]:
        """Setup test data before each test and cleanup after"""
        try:
            # Clear existing data
            result = await neo4j_test_session.run("MATCH (n) DETACH DELETE n")
            await result.consume()
            yield
        finally:
            # Cleanup after test
            result = await neo4j_test_session.run("MATCH (n) DETACH DELETE n")
            await result.consume()

    async def create_test_argument(
        self,
        neo4j_test_session: AsyncSession,
        argument_data: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Helper to create test argument in database"""
        argument_data = argument_data or settings.DEFAULT_TEST_ARGUMENT
        try:
            result = await neo4j_test_session.run("""
                CREATE (a:Argument {
                    claim: $claim,
                    grounds: $grounds,
                    warrant: $warrant
                })
                RETURN id(a) as argument_id
                """,
                claim=argument_data["claim"],
                grounds=argument_data["grounds"],
                warrant=argument_data["warrant"]
            )
            record = await result.single()
            await result.consume()
            if record is None:
                raise DatabaseError("Failed to create test argument: No record returned")
            return {"argument_id": record.get("argument_id")}
        except Exception as e:
            raise DatabaseError(f"Failed to create test argument: {str(e)}")

    @pytest.mark.asyncio
    async def test_verify_argument_structure(
        self,
        test_client: TestClient,
        neo4j_test_session: AsyncSession,
        valid_api_key: str
    ) -> None:
        """Test the structural verification endpoint"""
        # Insert test data
        argument = await self.create_test_argument(neo4j_test_session)
        
        response = test_client.post(
            "/verify-argument-structure",
            headers={"X-API-Key": valid_api_key},
            json={"argument_id": argument["argument_id"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "is_valid" in data
        assert isinstance(data["is_valid"], bool)

    @pytest.mark.asyncio
    async def test_verify_cyclic_structure(
        self,
        test_client: TestClient,
        neo4j_test_session: AsyncSession,
        valid_api_key: str
    ) -> None:
        """Test detection of cyclic arguments"""
        result = await neo4j_test_session.run("""
            CREATE (c1:Claim {text: 'Claim 1'})
            CREATE (c2:Claim {text: 'Claim 2'})
            CREATE (c3:Claim {text: 'Claim 3'})
            CREATE (c1)-[:SUPPORTS]->(c2)
            CREATE (c2)-[:SUPPORTS]->(c3)
            CREATE (c3)-[:SUPPORTS]->(c1)
            RETURN id(c1) as argument_id
        """)
        record = await result.single()
        await result.consume()
        
        if record is None:
            pytest.fail("No record returned from Neo4j query")
        
        # Safely extract argument_id using Record's keys method
        argument_id = record.get("argument_id")
        
        if argument_id is None:
            pytest.fail("No argument_id found in record")
        
        response = test_client.post(
            "/verify-argument-structure",
            headers={"X-API-Key": valid_api_key},
            json={"argument_id": argument_id}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error_type"] == "VALIDATION_ERROR"
        assert "cyclic" in data["detail"]["message"].lower()

    @pytest.mark.asyncio
    async def test_verify_orphaned_nodes(
        self,
        test_client: TestClient,
        neo4j_test_session: AsyncSession,
        valid_api_key: str
    ) -> None:
        """Test detection of orphaned nodes"""
        result = await neo4j_test_session.run("""
            CREATE (c1:Claim {text: 'Main Claim'})
            CREATE (c2:Claim {text: 'Orphaned Claim'})
            RETURN id(c1) as argument_id
        """)
        record = await result.single()
        await result.consume()
        
        if record is None:
            pytest.fail("No record returned from Neo4j query")
        
        # Safely extract argument_id using Record's keys method
        argument_id = record.get("argument_id")
        
        if argument_id is None:
            pytest.fail("No argument_id found in record")
        
        response = test_client.post(
            "/verify-argument-structure",
            headers={"X-API-Key": valid_api_key},
            json={"argument_id": argument_id}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error_type"] == "VALIDATION_ERROR"
        assert "orphaned" in data["detail"]["message"].lower()

    @pytest.mark.asyncio
    async def test_verify_complex_structure(
        self,
        test_client: TestClient,
        neo4j_test_session: AsyncSession,
        valid_api_key: str
    ) -> None:
        """Test verification of complex argument structure"""
        result = await neo4j_test_session.run("""
            CREATE (c1:Claim {text: 'Main Claim'})
            CREATE (c2:Claim {text: 'Supporting Claim 1'})
            CREATE (c3:Claim {text: 'Supporting Claim 2'})
            CREATE (c4:Claim {text: 'Supporting Claim 3'})
            CREATE (c2)-[:SUPPORTS]->(c1)
            CREATE (c3)-[:SUPPORTS]->(c1)
            CREATE (c4)-[:SUPPORTS]->(c2)
            RETURN id(c1) as argument_id
        """)
        record = await result.single()
        await result.consume()
        
        if record is None:
            pytest.fail("No record returned from Neo4j query")
        
        # Safely extract argument_id using Record's keys method
        argument_id = record.get("argument_id")
        
        if argument_id is None:
            pytest.fail("No argument_id found in record")
        
        response = test_client.post(
            "/verify-argument-structure",
            headers={"X-API-Key": valid_api_key},
            json={"argument_id": argument_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True

    @pytest.mark.asyncio
    async def test_database_error_handling(
        self,
        test_client: TestClient,
        neo4j_test_driver: AsyncDriver,
        valid_api_key: str
    ) -> None:
        """Test database error handling"""
        # Force database error by closing connection
        await neo4j_test_driver.close()
        
        response = test_client.post(
            "/verify-argument-structure",
            headers={"X-API-Key": valid_api_key},
            json={"argument_id": 999999}  # Non-existent ID
        )
        
        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["error_type"] == "DATABASE_ERROR"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("invalid_relation", [
        "UNKNOWN_RELATION",
        "INVALID_TYPE",
        "WRONG_CONNECTION"
    ])
    async def test_invalid_relationship_types(
        self,
        test_client: TestClient,
        neo4j_test_session: AsyncSession,
        valid_api_key: str,
        invalid_relation: str
    ) -> None:
        """Test handling of various invalid relationship types"""
        result = await neo4j_test_session.run(f"""
            CREATE (c1:Claim {{text: 'Test Claim'}})
            CREATE (c2:Claim {{text: 'Another Claim'}})
            CREATE (c1)-[:{invalid_relation}]->(c2)
            RETURN id(c1) as argument_id
        """)
        record = await result.single()
        await result.consume()
        
        if record is None:
            pytest.fail("No record returned from Neo4j query")
        
        # Safely extract argument_id using Record's keys method
        argument_id = record.get("argument_id")
        
        if argument_id is None:
            pytest.fail("No argument_id found in record")
        
        response = test_client.post(
            "/verify-argument-structure",
            headers={"X-API-Key": valid_api_key},
            json={"argument_id": argument_id}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error_type"] == "VALIDATION_ERROR"
        assert "relationship" in data["detail"]["message"].lower()

    def test_validation_error_handling(
        self,
        test_client: TestClient,
        valid_api_key: str
    ) -> None:
        """Test validation error handling"""
        response = test_client.post(
            "/verify-argument-structure",
            headers={"X-API-Key": valid_api_key},
            json={}  # Missing required argument_id
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "argument_id" in str(data["detail"]).lower()

    @pytest.mark.asyncio
    async def test_rate_limit_verification_endpoint(
        self,
        test_client: TestClient,
        valid_api_key: str
    ) -> None:
        """Test rate limiting on verification endpoint"""
        # Re-enable rate limiting for this test
        from rational_onion.api.main import limiter
        limiter.enabled = True
        try:
            responses = []
            rate_limit = int(settings.RATE_LIMIT.split('/')[0])

            for _ in range(rate_limit + 1):
                response = test_client.post(
                    "/verify-argument-structure",
                    headers={"X-API-Key": valid_api_key},
                    json={"argument_id": 1}
                )
                responses.append(response)
                await asyncio.sleep(0.1)  # Prevent overwhelming the server

            # Check that at least one response was rate limited
            assert any(r.status_code == 429 for r in responses)
            rate_limited_response = next(r for r in responses if r.status_code == 429)
            data: Dict[str, Any] = rate_limited_response.json()
            
            # Explicitly check the structure of the error response
            assert "detail" in data, "Error response is missing 'detail' key"
            assert isinstance(data["detail"], dict), "Detail should be a dictionary"
            assert "error_type" in data["detail"], "Detail is missing 'error_type'"
            assert data["detail"]["error_type"] == ErrorType.RATE_LIMIT_EXCEEDED
        finally:
            limiter.enabled = False

async def create_cyclic_structure(session: AsyncSession) -> None:
    """Create a test cyclic argument structure."""
    result = await session.run("""
        CREATE (c1:Claim {text: 'Claim 1'})
        CREATE (c2:Claim {text: 'Claim 2'})
        CREATE (c1)-[:SUPPORTS]->(c2)
        CREATE (c2)-[:SUPPORTS]->(c1)
    """)
    await result.consume()

async def create_orphaned_nodes(session: AsyncSession) -> None:
    """Create test orphaned nodes."""
    result = await session.run("""
        CREATE (c1:Claim {text: 'Connected Claim'})
        CREATE (g1:Grounds {text: 'Connected Grounds'})
        CREATE (g1)-[:SUPPORTS]->(c1)
        CREATE (c2:Claim {text: 'Orphaned Claim'})
        CREATE (w2:Warrant {text: 'Orphaned Warrant'})
    """)
    await result.consume()

async def create_complex_structure(session: AsyncSession) -> None:
    """Create a complex test argument structure."""
    result = await session.run("""
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
    await result.consume()

async def create_large_structure(session: AsyncSession) -> None:
    """Create a large test argument structure."""
    result = await session.run("""
        UNWIND range(1, 100) as i
        CREATE (c:Claim {text: 'Claim ' + toString(i)})
        WITH collect(c) as claims
        UNWIND range(0, size(claims)-2) as i
        WITH claims[i] as c1, claims[i+1] as c2
        CREATE (c1)-[:SUPPORTS]->(c2)
    """)
    await result.consume()
import pytest
from fastapi.testclient import TestClient
from rational_onion.api.main import app
from rational_onion.models.toulmin_model import ArgumentResponse
from rational_onion.api.errors import ErrorType, BaseAPIError
from rational_onion.config import get_test_settings
from neo4j import AsyncDriver, AsyncSession
from typing import AsyncGenerator, Dict, Any, List

settings = get_test_settings()

class TestArgumentProcessing:
    """Test suite for argument processing functionality"""
    
    @pytest.fixture(autouse=True)
    async def setup_test_data(self, neo4j_test_driver: AsyncDriver) -> AsyncGenerator[None, None]:
        """Setup and cleanup test data"""
        async with neo4j_test_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
        yield
        async with neo4j_test_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")

    @pytest.mark.asyncio
    async def test_insert_argument(
        self,
        test_client: TestClient,
        neo4j_test_session: AsyncSession,
        valid_api_key: str
    ) -> None:
        """Test inserting a new argument"""
        test_data = {
            "claim": "Test claim",
            "grounds": "Test grounds",
            "warrant": "Test warrant"
        }
        
        response = test_client.post(
            "/insert-argument",
            headers={"X-API-Key": valid_api_key},
            json=test_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "argument_id" in data
        assert isinstance(data["argument_id"], str)
        assert "message" in data
        assert data["message"] == "Argument created successfully"

    @pytest.mark.asyncio
    async def test_insert_argument_with_rebuttal(
        self,
        test_client: TestClient,
        valid_api_key: str
    ) -> None:
        """Test inserting argument with rebuttal"""
        test_data = {
            "claim": "Test claim",
            "grounds": "Test grounds",
            "warrant": "Test warrant",
            "rebuttal": "Test rebuttal"
        }
        
        response = test_client.post(
            "/insert-argument",
            headers={"X-API-Key": valid_api_key},
            json=test_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "argument_id" in data

    @pytest.mark.asyncio
    async def test_insert_argument_validation(
        self,
        test_client: TestClient,
        valid_api_key: str
    ) -> None:
        """Test argument validation during insertion"""
        # Test empty fields
        test_data = {
            "claim": "",
            "grounds": "",
            "warrant": ""
        }
        response = test_client.post(
            "/insert-argument",
            headers={"X-API-Key": valid_api_key},
            json=test_data
        )
        assert response.status_code == 422
        
        # Test exceeding max lengths
        test_data = {
            "claim": "a" * (settings.MAX_CLAIM_LENGTH + 1),
            "grounds": "b" * (settings.MAX_GROUNDS_LENGTH + 1),
            "warrant": "c" * (settings.MAX_WARRANT_LENGTH + 1)
        }
        response = test_client.post(
            "/insert-argument",
            headers={"X-API-Key": valid_api_key},
            json=test_data
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_insert_multiple_arguments(
        self,
        test_client: TestClient,
        neo4j_test_session: AsyncSession,
        valid_api_key: str
    ) -> None:
        """Test inserting multiple arguments"""
        argument_ids: List[str] = []
        
        # Insert multiple arguments
        for i in range(3):
            test_data = {
                "claim": f"Claim {i}",
                "grounds": f"Grounds {i}",
                "warrant": f"Warrant {i}"
            }
            response = test_client.post(
                "/insert-argument",
                headers={"X-API-Key": valid_api_key},
                json=test_data
            )
            assert response.status_code == 200
            data = response.json()
            argument_ids.append(data["argument_id"])
        
        # Verify all arguments were stored
        for arg_id in argument_ids:
            result = await neo4j_test_session.run(
                "MATCH (a:Claim) WHERE elementId(a) = $arg_id RETURN a",
                {"arg_id": arg_id}
            )
            record = await result.single()
            assert record is not None

    @pytest.mark.asyncio
    async def test_argument_relationships(
        self,
        test_client: TestClient,
        neo4j_test_session: AsyncSession,
        valid_api_key: str
    ) -> None:
        """Test creating relationships between arguments"""
        # Create two arguments
        arg1_data = {
            "claim": "Main claim",
            "grounds": "Main grounds",
            "warrant": "Main warrant"
        }
        arg2_data = {
            "claim": "Supporting claim",
            "grounds": "Supporting grounds",
            "warrant": "Supporting warrant"
        }
        
        # Insert arguments
        response1 = test_client.post(
            "/insert-argument",
            headers={"X-API-Key": valid_api_key},
            json=arg1_data
        )
        response2 = test_client.post(
            "/insert-argument",
            headers={"X-API-Key": valid_api_key},
            json=arg2_data
        )
        
        arg1_id = response1.json()["argument_id"]
        arg2_id = response2.json()["argument_id"]
        
        # Create relationship
        relationship_data = {
            "source_id": arg2_id,
            "target_id": arg1_id,
            "relationship_type": "SUPPORTS"
        }
        
        response = test_client.post(
            "/create-relationship",
            headers={"X-API-Key": valid_api_key},
            json=relationship_data
        )
        assert response.status_code == 200
        
        # Verify relationship was created
        result = await neo4j_test_session.run("""
            MATCH (a1:Claim)-[r:SUPPORTS]->(a2:Claim)
            WHERE elementId(a1) = $arg2_id AND elementId(a2) = $arg1_id
            RETURN r
        """, {"arg1_id": arg1_id, "arg2_id": arg2_id})
        record = await result.single()
        assert record is not None

    def test_unauthorized_access(self, test_client: TestClient) -> None:
        """Test unauthorized access to argument processing endpoints"""
        test_data = {
            "claim": "Test claim",
            "grounds": "Test grounds",
            "warrant": "Test warrant"
        }
        
        # Test without API key
        response = test_client.post("/insert-argument", json=test_data)
        assert response.status_code == 401
        
        # Test with invalid API key
        response = test_client.post(
            "/insert-argument",
            headers={"X-API-Key": "invalid_key"},
            json=test_data
        )
        assert response.status_code == 401

    def test_rate_limiting(self, test_client: TestClient, valid_api_key: str) -> None:
        """Test rate limiting on argument processing endpoints"""
        test_data = {
            "claim": "Test claim",
            "grounds": "Test grounds",
            "warrant": "Test warrant"
        }
        
        # Make multiple requests
        for _ in range(5):
            response = test_client.post(
                "/insert-argument",
                headers={"X-API-Key": valid_api_key},
                json=test_data
            )
            assert response.status_code == 200
        
        # Verify rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers

    query = """
    CREATE (a:Argument {claim: $claim})
    RETURN elementId(a) as argument_id
    """ 
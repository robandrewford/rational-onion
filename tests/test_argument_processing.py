import pytest
from fastapi.testclient import TestClient
from rational_onion.api.main import app
from rational_onion.models.toulmin_model import ArgumentResponse
from rational_onion.api.errors import ErrorType, BaseAPIError
from rational_onion.config import get_test_settings
from neo4j import AsyncDriver, AsyncSession
from typing import AsyncGenerator, Dict, Any

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

    def test_insert_argument_validation(self, test_client: TestClient, valid_api_key: str) -> None:
        """Tests input validation for argument insertion."""
        invalid_data = {
            "claim": "",  # Empty claim
            "grounds": "Some grounds",
            "warrant": "Some warrant"
        }
        response = test_client.post(
            "/insert-argument",
            json=invalid_data,
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert data["detail"]["error_type"] == ErrorType.VALIDATION_ERROR
        assert "field" in data["detail"]

    query = """
    CREATE (a:Argument {claim: $claim})
    RETURN elementId(a) as argument_id
    """ 
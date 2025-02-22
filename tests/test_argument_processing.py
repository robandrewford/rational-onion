import pytest
from fastapi.testclient import TestClient
from rational_onion.api.main import app
from rational_onion.models.toulmin_model import ArgumentResponse
from rational_onion.config import get_test_settings

settings = get_test_settings()

class TestArgumentProcessing:
    """Test suite for argument processing functionality"""
    
    @pytest.fixture(autouse=True)
    async def setup_test_data(self, neo4j_test_driver):
        """Setup and cleanup test data"""
        async with neo4j_test_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
        yield
        async with neo4j_test_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")

    def test_insert_argument(self, test_client, valid_api_key):
        """Test argument insertion"""
        response = test_client.post(
            "/insert-argument",
            headers={"X-API-Key": valid_api_key},
            json=settings.DEFAULT_TEST_ARGUMENT
        )
        assert response.status_code == 200
        self.assert_valid_argument_response(response.json(), settings.DEFAULT_TEST_ARGUMENT)

    @staticmethod
    def assert_valid_argument_response(response_data, input_data):
        """Validate argument response structure"""
        assert response_data["claim"] == input_data["claim"]
        assert response_data["grounds"] == input_data["grounds"]
        assert response_data["warrant"] == input_data["warrant"]
        assert response_data["rebuttal"] == input_data.get("rebuttal")
        assert "message" in response_data

def test_insert_argument_validation(test_client, valid_api_key):
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
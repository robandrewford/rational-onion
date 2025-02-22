import pytest
from fastapi.testclient import TestClient

def test_insert_argument(test_client, valid_api_key, sample_argument_data):
    """Tests argument insertion endpoint."""
    response = test_client.post(
        "/insert-argument",
        json=sample_argument_data,
        headers={"X-API-Key": valid_api_key}
    )
    assert response.status_code == 200
    assert_valid_argument_response(response.json(), sample_argument_data)

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

def assert_valid_argument_response(response_data, input_data):
    """Helper function to validate argument response."""
    assert response_data["claim"] == input_data["claim"]
    assert response_data["grounds"] == input_data["grounds"]
    assert response_data["warrant"] == input_data["warrant"]
    assert response_data["rebuttal"] == input_data.get("rebuttal")
    assert "message" in response_data 
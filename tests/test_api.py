# tests/test_api.py

import pytest
from fastapi.testclient import TestClient
from rational_onion.api.main import app

client = TestClient(app)

def test_insert_argument():
    response = client.post("/insert-argument", json={
        "claim": "AI regulation is necessary",
        "grounds": "Lack of regulations leads to bias",
        "warrant": "Regulations enforce fairness",
        "rebuttal": "Might slow innovation"
    }, headers={"X-API-Key": "abc123"})
    assert response.status_code == 200
    assert response.json()["message"] == "Argument successfully inserted."
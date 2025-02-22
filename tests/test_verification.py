# tests/test_verification.py

import pytest
from fastapi.testclient import TestClient
from rational_onion.api.main import app

client = TestClient(app)

def test_verify_argument_structure():
    """
    Tests the structural verification endpoint (cycles & orphaned nodes).
    """
    response = client.get("/verify-argument-structure", headers={"X-API-Key": "abc123"})
    assert response.status_code == 200, "Verification endpoint should return 200"
    
    data = response.json()
    assert "has_cycles" in data, "Response missing 'has_cycles' field"
    assert "orphaned_nodes" in data, "Response missing 'orphaned_nodes' field"

    # Example checks
    has_cycles = data["has_cycles"]
    orphaned_nodes = data["orphaned_nodes"]

    assert isinstance(has_cycles, bool), "'has_cycles' should be boolean"
    assert isinstance(orphaned_nodes, list), "'orphaned_nodes' should be a list"

    # If you have some known data setup, you can assert expected values:
    # assert not has_cycles, "Expected no cycles with sample data"
    # assert orphaned_nodes == [], "Expected no orphaned nodes with sample data"
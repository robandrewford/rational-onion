# tests/test_dag.py

import pytest
from fastapi.testclient import TestClient
from rational_onion.api.main import app

# Remove global client initialization
# client = TestClient(app)

def test_dag_visualization(test_client, valid_api_key):
    """
    Tests the DAG retrieval endpoint that returns nodes and edges for visualization.
    """
    response = test_client.get(
        "/visualize-dag",
        headers={"X-API-Key": valid_api_key}
    )
    assert response.status_code == 200, "DAG endpoint should return 200"
    
    data = response.json()
    assert "nodes" in data, "DAG response should contain nodes"
    assert "edges" in data, "DAG response should contain edges"

    # Basic assertion: empty or actual
    assert isinstance(data["nodes"], list), "Nodes should be a list"
    assert isinstance(data["edges"], list), "Edges should be a list"
# tests/test_dag.py

import pytest
from fastapi.testclient import TestClient
from rational_onion.api.main import app

client = TestClient(app)

def test_dag_visualization():
    """
    Tests the DAG retrieval endpoint that returns nodes and edges for visualization.
    """
    response = client.get("/visualize-argument-dag", headers={"X-API-Key": "hey@309"})
    assert response.status_code == 200, "DAG endpoint should return 200"
    
    data = response.json()
    assert "nodes" in data, "DAG response should contain nodes"
    assert "edges" in data, "DAG response should contain edges"

    # Basic assertion: empty or actual
    assert isinstance(data["nodes"], list), "Nodes should be a list"
    assert isinstance(data["edges"], list), "Edges should be a list"
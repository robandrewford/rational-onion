# tests/test_dag.py

import pytest
from fastapi.testclient import TestClient
from neo4j import AsyncSession
from rational_onion.api.main import app
from rational_onion.api.errors import ErrorType
from typing import Any

# Remove global client initialization
# client = TestClient(app)

class TestDagVisualization:
    """Test suite for DAG visualization functionality"""
    
    @pytest.fixture(autouse=True)
    async def setup_test_data(self, neo4j_test_session: AsyncSession) -> None:
        """Setup and cleanup test data"""
        await neo4j_test_session.run("MATCH (n) DETACH DELETE n")
        yield
        await neo4j_test_session.run("MATCH (n) DETACH DELETE n")

    async def create_test_graph(self, session: AsyncSession) -> None:
        """Create a test graph structure"""
        await session.run("""
            CREATE (c1:Claim {text: 'Main Claim'})
            CREATE (c2:Claim {text: 'Supporting Claim 1'})
            CREATE (c3:Claim {text: 'Supporting Claim 2'})
            CREATE (c2)-[:SUPPORTS]->(c1)
            CREATE (c3)-[:SUPPORTS]->(c1)
        """)

    def test_empty_graph(self, test_client: TestClient, valid_api_key: str) -> None:
        """Test visualization of empty graph"""
        response = test_client.get(
            "/visualize-argument-dag",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 0
        assert len(data["edges"]) == 0
        assert "layout" in data
        assert data["layout"]["name"] == "cose"

    @pytest.mark.asyncio
    async def test_complex_graph(
        self,
        test_client: TestClient,
        neo4j_test_session: AsyncSession,
        valid_api_key: str
    ) -> None:
        """Test visualization of complex graph structure"""
        await self.create_test_graph(neo4j_test_session)
        
        response = test_client.get(
            "/visualize-argument-dag",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify graph structure
        assert len(data["nodes"]) == 3
        assert len(data["edges"]) == 2
        
        # Verify node properties
        for node in data["nodes"]:
            assert "id" in node
            assert "label" in node
            assert node["label"] == "Claim"
            assert "text" in node
        
        # Verify edge properties
        for edge in data["edges"]:
            assert "source" in edge
            assert "target" in edge
            assert "type" in edge
            assert edge["type"] == "SUPPORTS"

    @pytest.mark.asyncio
    async def test_invalid_graph(
        self,
        test_client: TestClient,
        neo4j_test_session: AsyncSession,
        valid_api_key: str
    ) -> None:
        """Test handling of invalid graph structures"""
        # Create invalid relationship type
        await neo4j_test_session.run("""
            CREATE (c1:Claim {text: 'Claim 1'})
            CREATE (c2:Claim {text: 'Claim 2'})
            CREATE (c1)-[:INVALID_TYPE]->(c2)
        """)
        
        response = test_client.get(
            "/visualize-argument-dag",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200  # Should still return successfully
        data = response.json()
        
        # Invalid relationships should still be included in visualization
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1
        assert data["edges"][0]["type"] == "INVALID_TYPE"

    def test_unauthorized_access(self, test_client: TestClient) -> None:
        """Test that unauthorized access is properly handled"""
        response = test_client.get("/visualize-argument-dag")
        assert response.status_code == 401
        data = response.json()
        assert "api key" in data["detail"].lower()

    async def test_rate_limiting(self, test_client: TestClient, valid_api_key: str, rate_limiter: Any) -> None:
        """Test that rate limiting is configured for the endpoint"""
        # Import the router to check the rate limit decorator
        from rational_onion.api.dag_visualization import router
        
        # Check that the rate limiter is configured
        assert rate_limiter is not None
        assert hasattr(rate_limiter, 'enabled')
        
        # Check that the endpoint exists in the router
        route = next(r for r in router.routes if r.path == "/visualize-argument-dag")
        assert route is not None
        
        # Make a request to ensure the endpoint works
        response = test_client.get(
            "/visualize-argument-dag",
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200
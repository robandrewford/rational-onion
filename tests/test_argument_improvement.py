# tests/test_argument_improvement.py

import pytest
from fastapi.testclient import TestClient
from neo4j import AsyncDriver, AsyncSession
from typing import AsyncGenerator, Dict, Any, List
from unittest.mock import patch, MagicMock
import json

from rational_onion.api.main import app
from rational_onion.config import get_test_settings
from rational_onion.services.nlp_service import enhance_argument_with_nlp

settings = get_test_settings()

class TestArgumentImprovement:
    """Test suite for argument improvement functionality"""
    
    @pytest.fixture(autouse=True)
    async def setup_test_data(self, neo4j_test_session: AsyncSession) -> AsyncGenerator[None, None]:
        """Setup and cleanup test data"""
        # Clear database before test
        await neo4j_test_session.run("MATCH (n) DETACH DELETE n")
        
        # Create test arguments
        await self.create_test_arguments(neo4j_test_session)
        
        yield
        
        # Clean up after test
        await neo4j_test_session.run("MATCH (n) DETACH DELETE n")
    
    async def create_test_arguments(self, session: AsyncSession) -> None:
        """Create test arguments in the database"""
        await session.run("""
            CREATE (c1:Claim {text: 'Climate change is primarily caused by human activities.'})
            CREATE (c2:Claim {text: 'Renewable energy is more sustainable than fossil fuels.'})
            CREATE (c3:Claim {text: 'Electric vehicles reduce carbon emissions.'})
            CREATE (g1:Ground {text: 'CO2 levels have increased since the industrial revolution.'})
            CREATE (g2:Ground {text: 'Solar and wind energy do not deplete natural resources.'})
            CREATE (g3:Ground {text: 'EVs produce zero tailpipe emissions.'})
            CREATE (w1:Warrant {text: 'Industrial activities release greenhouse gases.'})
            CREATE (w2:Warrant {text: 'Sustainability means meeting present needs without compromising future generations.'})
            CREATE (w3:Warrant {text: 'Reduced carbon emissions help mitigate climate change.'})
            
            CREATE (c1)-[:HAS_GROUND]->(g1)
            CREATE (c2)-[:HAS_GROUND]->(g2)
            CREATE (c3)-[:HAS_GROUND]->(g3)
            CREATE (c1)-[:HAS_WARRANT]->(w1)
            CREATE (c2)-[:HAS_WARRANT]->(w2)
            CREATE (c3)-[:HAS_WARRANT]->(w3)
            CREATE (c2)-[:SUPPORTS]->(c1)
            CREATE (c3)-[:SUPPORTS]->(c2)
        """)
    
    @pytest.mark.asyncio
    async def test_suggest_improvements_all_arguments(
        self,
        test_client: TestClient,
        valid_api_key: str
    ) -> None:
        """Test getting improvement suggestions for all arguments"""
        with patch('rational_onion.services.nlp_service.enhance_argument_with_nlp') as mock_enhance:
            # Mock the NLP enhancement function
            mock_enhance.return_value = [
                "Add more specific evidence to strengthen your claim.",
                "Consider addressing potential counterarguments."
            ]
            
            response = test_client.get(
                "/suggest-improvements",
                headers={"X-API-Key": valid_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "quality_score" in data
            assert "improvement_suggestions" in data
            assert isinstance(data["improvement_suggestions"], list)
            assert len(data["improvement_suggestions"]) > 0
            
            # Verify each suggestion has the expected structure
            for suggestion in data["improvement_suggestions"]:
                assert "claim" in suggestion
                assert "improvement_suggestions" in suggestion
                assert isinstance(suggestion["improvement_suggestions"], list)
                assert len(suggestion["improvement_suggestions"]) > 0
    
    @pytest.mark.asyncio
    async def test_suggest_improvements_specific_argument(
        self,
        test_client: TestClient,
        neo4j_test_session: AsyncSession,
        valid_api_key: str
    ) -> None:
        """Test getting improvement suggestions for a specific argument"""
        # First, get an argument ID
        result = await neo4j_test_session.run("""
            MATCH (c:Claim {text: 'Climate change is primarily caused by human activities.'})
            RETURN elementId(c) as id
        """)
        record = await result.single()
        argument_id = record["id"]
        
        with patch('rational_onion.services.nlp_service.enhance_argument_with_nlp') as mock_enhance:
            # Mock the NLP enhancement function
            mock_enhance.return_value = [
                "Provide more recent scientific evidence.",
                "Quantify the human contribution to greenhouse gas emissions."
            ]
            
            response = test_client.get(
                f"/suggest-improvements?argument_id={argument_id}",
                headers={"X-API-Key": valid_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "quality_score" in data
            assert "improvement_suggestions" in data
            assert isinstance(data["improvement_suggestions"], list)
            assert len(data["improvement_suggestions"]) == 1  # Should only have one suggestion for the specific argument
            
            # Verify the suggestion is for the correct argument
            suggestion = data["improvement_suggestions"][0]
            assert suggestion["claim"] == "Climate change is primarily caused by human activities."
            assert len(suggestion["improvement_suggestions"]) == 2
    
    @pytest.mark.asyncio
    async def test_suggest_improvements_invalid_argument_id(
        self,
        test_client: TestClient,
        valid_api_key: str
    ) -> None:
        """Test getting improvement suggestions with an invalid argument ID"""
        response = test_client.get(
            "/suggest-improvements?argument_id=invalid_id",
            headers={"X-API-Key": valid_api_key}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "error_type" in data["detail"]
        assert data["detail"]["error_type"] == "VALIDATION_ERROR"
    
    @pytest.mark.asyncio
    async def test_suggest_improvements_missing_components(
        self,
        test_client: TestClient,
        neo4j_test_session: AsyncSession,
        valid_api_key: str
    ) -> None:
        """Test getting improvement suggestions for arguments with missing components"""
        # Create an argument with missing components
        await neo4j_test_session.run("""
            CREATE (c:Claim {text: 'Incomplete argument without proper support.'})
        """)
        
        with patch('rational_onion.services.nlp_service.enhance_argument_with_nlp') as mock_enhance:
            # Mock the NLP enhancement function
            mock_enhance.return_value = [
                "Add grounds to support your claim.",
                "Provide a warrant to connect your grounds to your claim."
            ]
            
            response = test_client.get(
                "/suggest-improvements",
                headers={"X-API-Key": valid_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify missing components are identified
            assert "missing_components" in data
            assert isinstance(data["missing_components"], list)
            assert len(data["missing_components"]) > 0
            
            # Verify the incomplete argument is in the suggestions
            found_incomplete = False
            for suggestion in data["improvement_suggestions"]:
                if suggestion["claim"] == "Incomplete argument without proper support.":
                    found_incomplete = True
                    assert "Add grounds" in suggestion["improvement_suggestions"][0]
                    break
            
            assert found_incomplete, "The incomplete argument should be in the suggestions"
    
    def test_unauthorized_access(self, test_client: TestClient) -> None:
        """Test unauthorized access to improvement suggestions endpoint"""
        # Test without API key
        response = test_client.get("/suggest-improvements")
        assert response.status_code == 401
        
        # Test with invalid API key
        response = test_client.get(
            "/suggest-improvements",
            headers={"X-API-Key": "invalid_key"}
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_nlp_service_integration(
        self,
        test_client: TestClient,
        valid_api_key: str
    ) -> None:
        """Test integration with the NLP service"""
        # Test the actual NLP service function (not mocked)
        test_text = "Climate change is a serious issue."
        suggestions = enhance_argument_with_nlp(test_text)
        
        # Verify the NLP service returns suggestions
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Now test the API endpoint with the real NLP service
        response = test_client.get(
            "/suggest-improvements",
            headers={"X-API-Key": valid_api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "quality_score" in data
        assert "improvement_suggestions" in data
        assert isinstance(data["improvement_suggestions"], list) 
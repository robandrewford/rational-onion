import pytest
from fastapi.testclient import TestClient
from rational_onion.api.main import app
from rational_onion.models.toulmin_model import ArgumentResponse
from rational_onion.api.errors import ErrorType, BaseAPIError
from rational_onion.config import get_test_settings
from neo4j import AsyncDriver, AsyncSession
from typing import AsyncGenerator, Dict, Any, List
import logging

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

    @pytest.mark.asyncio(scope="function")
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

    @pytest.mark.asyncio(scope="function")
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

    @pytest.mark.asyncio(scope="function")
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

    @pytest.mark.asyncio(scope="function")
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
                "MATCH (a:Argument) WHERE elementId(a) = $arg_id RETURN a",
                {"arg_id": arg_id}
            )
            record = await result.single()
            assert record is not None

    @pytest.mark.asyncio(scope="function")
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
            MATCH (a1:Argument)-[r:SUPPORTS]->(a2:Argument)
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

    def test_rate_limiting(self, test_client: TestClient, valid_api_key: str, rate_limiter: Any) -> None:
        """Test rate limiting configuration on argument processing endpoints"""
        from rational_onion.api.main import app
        from rational_onion.api.rate_limiting import limiter
        
        # Verify that the rate limiter is configured in the app
        assert hasattr(app.state, "limiter"), "App should have limiter in state"
        assert app.state.limiter is not None, "Rate limiter should be configured"
        
        # Verify that the rate limiter is configured correctly
        assert hasattr(rate_limiter, "enabled"), "Rate limiter should have enabled attribute"
        
        # Verify that the rate limiter is properly initialized
        assert rate_limiter is limiter, "Rate limiter in app state should be the same as the one in rate_limiting.py"
        
        # Make a basic request to ensure the endpoint works
        test_data = {
            "claim": "Test claim",
            "grounds": "Test grounds",
            "warrant": "Test warrant"
        }
        
        # Enable rate limiting for this test
        original_enabled = rate_limiter.enabled
        rate_limiter.enabled = True
        
        try:
            response = test_client.post(
                "/insert-argument",
                headers={"X-API-Key": valid_api_key},
                json=test_data
            )
            
            # Just verify the endpoint works, not checking rate limit headers
            assert response.status_code == 200, "Endpoint should return 200 OK"
        finally:
            # Restore original state
            rate_limiter.enabled = original_enabled
            
    @pytest.mark.asyncio(scope="function")
    async def test_relationship_validation(
        self,
        test_client: TestClient,
        neo4j_test_session: AsyncSession,
        valid_api_key: str
    ) -> None:
        """Test validation of relationship types and properties"""
        # Create two arguments
        arg1_response = test_client.post(
            "/insert-argument",
            headers={"X-API-Key": valid_api_key},
            json={"claim": "Claim 1", "grounds": "Grounds 1", "warrant": "Warrant 1"}
        )
        arg1_data = arg1_response.json()
        arg1_id = arg1_data["argument_id"]
        
        arg2_response = test_client.post(
            "/insert-argument",
            headers={"X-API-Key": valid_api_key},
            json={"claim": "Claim 2", "grounds": "Grounds 2", "warrant": "Warrant 2"}
        )
        arg2_data = arg2_response.json()
        arg2_id = arg2_data["argument_id"]
        
        # Test invalid relationship type
        response = test_client.post(
            "/create-relationship",
            headers={"X-API-Key": valid_api_key},
            json={"source_id": arg1_id, "target_id": arg2_id, "relationship_type": "INVALID_TYPE"}
        )
        assert response.status_code == 422
        error_data = response.json()
        print("Invalid relationship type error response:", error_data)
        assert "detail" in error_data
        assert "error_type" in error_data["detail"]
        assert "message" in error_data["detail"]
        assert "Invalid relationship type" in error_data["detail"]["message"]
        
        # Test self-referential relationship
        response = test_client.post(
            "/create-relationship",
            headers={"X-API-Key": valid_api_key},
            json={"source_id": arg1_id, "target_id": arg1_id, "relationship_type": "SUPPORTS"}
        )
        assert response.status_code == 422
        error_data = response.json()
        print("Self-referential relationship error response:", error_data)
        assert "detail" in error_data
        assert "error_type" in error_data["detail"]
        assert "message" in error_data["detail"]
        assert "Self-referential" in error_data["detail"]["message"]

    @pytest.mark.asyncio(scope="function")
    async def test_argument_validation(
        self,
        test_client: TestClient,
        neo4j_test_session: AsyncSession,
        valid_api_key: str
    ) -> None:
        """Test validation of argument fields"""
        # Test argument with empty claim
        response = test_client.post(
            "/insert-argument",
            headers={"X-API-Key": valid_api_key},
            json={"claim": "", "grounds": "Test grounds", "warrant": "Test warrant"}
        )
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
        assert error_data["detail"]["error_type"] == "VALIDATION_ERROR"
        assert "errors" in error_data["detail"]
        
        # Test argument with claim exceeding maximum length
        settings = get_test_settings()
        long_claim = "A" * (settings.MAX_CLAIM_LENGTH + 1)
        response = test_client.post(
            "/insert-argument",
            headers={"X-API-Key": valid_api_key},
            json={"claim": long_claim, "grounds": "Test grounds", "warrant": "Test warrant"}
        )
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
        assert error_data["detail"]["error_type"] == "VALIDATION_ERROR"
        assert "errors" in error_data["detail"]
        
        # Check if any error contains max_length validation
        has_max_length_error = False
        for error in error_data["detail"]["errors"]:
            if "type" in error and ("max_length" in error["type"] or "value_error.any_str.max_length" in error["type"]):
                has_max_length_error = True
                break
        assert has_max_length_error, f"No max_length error found in: {error_data['detail']['errors']}"
        
        # Test argument with grounds exceeding maximum length
        long_grounds = "A" * (settings.MAX_GROUNDS_LENGTH + 1)
        response = test_client.post(
            "/insert-argument",
            headers={"X-API-Key": valid_api_key},
            json={"claim": "Test claim", "grounds": long_grounds, "warrant": "Test warrant"}
        )
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
        assert error_data["detail"]["error_type"] == "VALIDATION_ERROR"
        assert "errors" in error_data["detail"]
        
        # Check if any error contains max_length validation
        has_max_length_error = False
        for error in error_data["detail"]["errors"]:
            if "type" in error and ("max_length" in error["type"] or "value_error.any_str.max_length" in error["type"]):
                has_max_length_error = True
                break
        assert has_max_length_error, f"No max_length error found in: {error_data['detail']['errors']}"
        
        # Test argument with warrant exceeding maximum length
        long_warrant = "A" * (settings.MAX_WARRANT_LENGTH + 1)
        response = test_client.post(
            "/insert-argument",
            headers={"X-API-Key": valid_api_key},
            json={"claim": "Test claim", "grounds": "Test grounds", "warrant": long_warrant}
        )
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
        assert error_data["detail"]["error_type"] == "VALIDATION_ERROR"
        assert "errors" in error_data["detail"]
        
        # Check if any error contains max_length validation
        has_max_length_error = False
        for error in error_data["detail"]["errors"]:
            if "type" in error and ("max_length" in error["type"] or "value_error.any_str.max_length" in error["type"]):
                has_max_length_error = True
                break
        assert has_max_length_error, f"No max_length error found in: {error_data['detail']['errors']}"

    @pytest.mark.asyncio(scope="function")
    async def test_create_relationship(
        self,
        test_client: TestClient,
        neo4j_test_session: AsyncSession,
        valid_api_key: str
    ) -> None:
        """Test creating relationships between arguments"""
        # Create two arguments first
        arg1_response = test_client.post(
            "/insert-argument",
            headers={"X-API-Key": valid_api_key},
            json={"claim": "First claim", "grounds": "First grounds", "warrant": "First warrant"}
        )
        assert arg1_response.status_code == 200
        arg1_data = arg1_response.json()
        arg1_id = arg1_data["argument_id"]
        
        arg2_response = test_client.post(
            "/insert-argument",
            headers={"X-API-Key": valid_api_key},
            json={"claim": "Second claim", "grounds": "Second grounds", "warrant": "Second warrant"}
        )
        assert arg2_response.status_code == 200
        arg2_data = arg2_response.json()
        arg2_id = arg2_data["argument_id"]
        
        # Test creating a SUPPORTS relationship
        supports_response = test_client.post(
            "/create-relationship",
            headers={"X-API-Key": valid_api_key},
            json={"source_id": arg1_id, "target_id": arg2_id, "relationship_type": "SUPPORTS"}
        )
        assert supports_response.status_code == 200
        supports_data = supports_response.json()
        assert "relationship_id" in supports_data
        assert "message" in supports_data
        
        # Test creating a CHALLENGES relationship
        challenges_response = test_client.post(
            "/create-relationship",
            headers={"X-API-Key": valid_api_key},
            json={"source_id": arg2_id, "target_id": arg1_id, "relationship_type": "CHALLENGES"}
        )
        assert challenges_response.status_code == 200
        challenges_data = challenges_response.json()
        assert "relationship_id" in challenges_data
        assert "message" in challenges_data
        
        # Test creating a JUSTIFIES relationship
        justifies_response = test_client.post(
            "/create-relationship",
            headers={"X-API-Key": valid_api_key},
            json={"source_id": arg1_id, "target_id": arg1_id, "relationship_type": "JUSTIFIES"}
        )
        # This should fail because it's self-referential
        assert justifies_response.status_code == 422
        justifies_data = justifies_response.json()
        assert "detail" in justifies_data
        assert justifies_data["detail"]["error_type"] == "VALIDATION_ERROR"
        
        # Verify relationships in the database
        query = """
        MATCH (a1:Argument)-[r]->(a2:Argument)
        WHERE elementId(a1) = $arg1_id AND elementId(a2) = $arg2_id
        RETURN type(r) as relationship_type
        """
        result = await neo4j_test_session.run(query, {"arg1_id": arg1_id, "arg2_id": arg2_id})
        record = await result.single()
        assert record is not None
        assert record["relationship_type"] == "SUPPORTS"
        
        query = """
        MATCH (a1:Argument)-[r]->(a2:Argument)
        WHERE elementId(a1) = $arg2_id AND elementId(a2) = $arg1_id
        RETURN type(r) as relationship_type
        """
        result = await neo4j_test_session.run(query, {"arg2_id": arg2_id, "arg1_id": arg1_id})
        record = await result.single()
        assert record is not None
        assert record["relationship_type"] == "CHALLENGES"

    @pytest.mark.asyncio(scope="function")
    async def test_invalid_relationship_type(
        self,
        test_client: TestClient,
        neo4j_test_session: AsyncSession,
        valid_api_key: str
    ) -> None:
        """Test validation of relationship types"""
        # Create two arguments first
        arg1_response = test_client.post(
            "/insert-argument",
            headers={"X-API-Key": valid_api_key},
            json={"claim": "First claim", "grounds": "First grounds", "warrant": "First warrant"}
        )
        assert arg1_response.status_code == 200
        arg1_data = arg1_response.json()
        arg1_id = arg1_data["argument_id"]
        
        arg2_response = test_client.post(
            "/insert-argument",
            headers={"X-API-Key": valid_api_key},
            json={"claim": "Second claim", "grounds": "Second grounds", "warrant": "Second warrant"}
        )
        assert arg2_response.status_code == 200
        arg2_data = arg2_response.json()
        arg2_id = arg2_data["argument_id"]
        
        # Test with an invalid relationship type
        response = test_client.post(
            "/create-relationship",
            headers={"X-API-Key": valid_api_key},
            json={"source_id": arg1_id, "target_id": arg2_id, "relationship_type": "INVALID_TYPE"}
        )
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
        assert error_data["detail"]["error_type"] == "VALIDATION_ERROR"
        assert "field" in error_data["detail"]["details"]
        assert error_data["detail"]["details"]["field"] == "relationship_type"
        
        # Test with a non-existent argument ID
        response = test_client.post(
            "/create-relationship",
            headers={"X-API-Key": valid_api_key},
            json={"source_id": "non-existent-id", "target_id": arg2_id, "relationship_type": "SUPPORTS"}
        )
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
        assert error_data["detail"]["error_type"] == "VALIDATION_ERROR"
        assert "field" in error_data["detail"]["details"]
        assert error_data["detail"]["details"]["field"] == "source_id/target_id"
        
        # Verify no relationships were created
        query = """
        MATCH (a1:Argument)-[r]->(a2:Argument)
        WHERE elementId(a1) = $arg1_id AND elementId(a2) = $arg2_id
        RETURN count(r) as relationship_count
        """
        result = await neo4j_test_session.run(query, {"arg1_id": arg1_id, "arg2_id": arg2_id})
        record = await result.single()
        # Should be 0 because we didn't create any valid relationships in this test
        # (Any relationships would have been created in other tests)
        assert record["relationship_count"] == 0

    @pytest.mark.asyncio(scope="function")
    async def test_relationship_uniqueness(
        self,
        test_client: TestClient,
        neo4j_test_session: AsyncSession,
        valid_api_key: str
    ) -> None:
        """Test handling of duplicate relationships between the same arguments"""
        # Create two arguments first
        arg1_response = test_client.post(
            "/insert-argument",
            headers={"X-API-Key": valid_api_key},
            json={"claim": "First claim", "grounds": "First grounds", "warrant": "First warrant"}
        )
        assert arg1_response.status_code == 200
        arg1_data = arg1_response.json()
        arg1_id = arg1_data["argument_id"]
        
        arg2_response = test_client.post(
            "/insert-argument",
            headers={"X-API-Key": valid_api_key},
            json={"claim": "Second claim", "grounds": "Second grounds", "warrant": "Second warrant"}
        )
        assert arg2_response.status_code == 200
        arg2_data = arg2_response.json()
        arg2_id = arg2_data["argument_id"]
        
        # Create first relationship
        first_response = test_client.post(
            "/create-relationship",
            headers={"X-API-Key": valid_api_key},
            json={"source_id": arg1_id, "target_id": arg2_id, "relationship_type": "SUPPORTS"}
        )
        assert first_response.status_code == 200
        first_data = first_response.json()
        assert "relationship_id" in first_data
        first_relationship_id = first_data["relationship_id"]
        
        # Create duplicate relationship (same source, target, and type)
        duplicate_response = test_client.post(
            "/create-relationship",
            headers={"X-API-Key": valid_api_key},
            json={"source_id": arg1_id, "target_id": arg2_id, "relationship_type": "SUPPORTS"}
        )
        assert duplicate_response.status_code == 200
        duplicate_data = duplicate_response.json()
        assert "relationship_id" in duplicate_data
        duplicate_relationship_id = duplicate_data["relationship_id"]
        
        # The system currently allows duplicate relationships, so we're just verifying
        # that both were created successfully but have different IDs
        assert first_relationship_id != duplicate_relationship_id
        
        # Verify that two relationships were created in the database
        query = """
        MATCH (a1:Argument)-[r:SUPPORTS]->(a2:Argument)
        WHERE elementId(a1) = $arg1_id AND elementId(a2) = $arg2_id
        RETURN count(r) as relationship_count
        """
        result = await neo4j_test_session.run(query, {"arg1_id": arg1_id, "arg2_id": arg2_id})
        record = await result.single()
        assert record is not None
        assert record["relationship_count"] == 2
        
        # Create a different type of relationship between the same arguments
        different_type_response = test_client.post(
            "/create-relationship",
            headers={"X-API-Key": valid_api_key},
            json={"source_id": arg1_id, "target_id": arg2_id, "relationship_type": "CHALLENGES"}
        )
        assert different_type_response.status_code == 200
        
        # Verify that now there are three relationships in total
        query = """
        MATCH (a1:Argument)-[r]->(a2:Argument)
        WHERE elementId(a1) = $arg1_id AND elementId(a2) = $arg2_id
        RETURN count(r) as relationship_count
        """
        result = await neo4j_test_session.run(query, {"arg1_id": arg1_id, "arg2_id": arg2_id})
        record = await result.single()
        assert record is not None
        assert record["relationship_count"] == 3

    @pytest.mark.asyncio(scope="function")
    async def test_complex_relationship_chain(
        self,
        test_client: TestClient,
        neo4j_test_session: AsyncSession,
        valid_api_key: str
    ) -> None:
        """Test creating and validating complex chains of relationships between multiple arguments"""
        # Create four arguments to form a chain
        arguments = []
        for i in range(4):
            response = test_client.post(
                "/insert-argument",
                headers={"X-API-Key": valid_api_key},
                json={
                    "claim": f"Claim {i}",
                    "grounds": f"Grounds {i}",
                    "warrant": f"Warrant {i}"
                }
            )
            assert response.status_code == 200
            data = response.json()
            arguments.append(data["argument_id"])
        
        # Create a chain of relationships: A supports B, B challenges C, C justifies D
        relationships = [
            {"source_id": arguments[0], "target_id": arguments[1], "relationship_type": "SUPPORTS"},
            {"source_id": arguments[1], "target_id": arguments[2], "relationship_type": "CHALLENGES"},
            {"source_id": arguments[2], "target_id": arguments[3], "relationship_type": "JUSTIFIES"}
        ]
        
        for rel in relationships:
            response = test_client.post(
                "/create-relationship",
                headers={"X-API-Key": valid_api_key},
                json=rel
            )
            assert response.status_code == 200
            data = response.json()
            assert "relationship_id" in data
        
        # Verify the chain in the database
        query = """
        MATCH path = (a1:Argument)-[:SUPPORTS]->(a2:Argument)-[:CHALLENGES]->(a3:Argument)-[:JUSTIFIES]->(a4:Argument)
        WHERE elementId(a1) = $arg0_id AND elementId(a2) = $arg1_id 
          AND elementId(a3) = $arg2_id AND elementId(a4) = $arg3_id
        RETURN count(path) as path_count
        """
        result = await neo4j_test_session.run(query, {
            "arg0_id": arguments[0],
            "arg1_id": arguments[1],
            "arg2_id": arguments[2],
            "arg3_id": arguments[3]
        })
        record = await result.single()
        assert record is not None
        assert record["path_count"] == 1
        
        # Create a circular relationship to complete the cycle: D supports A
        response = test_client.post(
            "/create-relationship",
            headers={"X-API-Key": valid_api_key},
            json={"source_id": arguments[3], "target_id": arguments[0], "relationship_type": "SUPPORTS"}
        )
        assert response.status_code == 200
        
        # Verify the circular relationship
        query = """
        MATCH path = (a1:Argument)-[:SUPPORTS]->(a2:Argument)-[:CHALLENGES]->(a3:Argument)-[:JUSTIFIES]->(a4:Argument)-[:SUPPORTS]->(a1)
        WHERE elementId(a1) = $arg0_id AND elementId(a2) = $arg1_id 
          AND elementId(a3) = $arg2_id AND elementId(a4) = $arg3_id
        RETURN count(path) as cycle_count
        """
        result = await neo4j_test_session.run(query, {
            "arg0_id": arguments[0],
            "arg1_id": arguments[1],
            "arg2_id": arguments[2],
            "arg3_id": arguments[3]
        })
        record = await result.single()
        assert record is not None
        assert record["cycle_count"] == 1

    @pytest.mark.asyncio(scope="function")
    async def test_concurrent_argument_creation(
        self,
        test_client: TestClient,
        neo4j_test_session: AsyncSession,
        valid_api_key: str
    ) -> None:
        """Test the system's ability to handle multiple concurrent argument creations"""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        # Number of concurrent argument creations
        num_arguments = 10
        
        # Function to create an argument
        def create_argument(i):
            response = test_client.post(
                "/insert-argument",
                headers={"X-API-Key": valid_api_key},
                json={
                    "claim": f"Concurrent claim {i}",
                    "grounds": f"Concurrent grounds {i}",
                    "warrant": f"Concurrent warrant {i}"
                }
            )
            return response.status_code, response.json()
        
        # Create arguments concurrently using a thread pool
        argument_ids = []
        with ThreadPoolExecutor(max_workers=num_arguments) as executor:
            futures = [executor.submit(create_argument, i) for i in range(num_arguments)]
            for future in futures:
                status_code, data = future.result()
                assert status_code == 200
                assert "argument_id" in data
                argument_ids.append(data["argument_id"])
        
        # Verify that all arguments were created in the database
        query = """
        MATCH (a:Argument)
        WHERE a.claim STARTS WITH 'Concurrent claim'
        RETURN count(a) as argument_count
        """
        result = await neo4j_test_session.run(query)
        record = await result.single()
        assert record is not None
        assert record["argument_count"] == num_arguments
        
        # Verify that each argument has a unique ID
        assert len(argument_ids) == num_arguments
        assert len(set(argument_ids)) == num_arguments  # All IDs should be unique

    @pytest.mark.asyncio(scope="function")
    async def test_api_key_rotation(
        self,
        test_client: TestClient,
        valid_api_key: str
    ) -> None:
        """Test API key rotation and validation"""
        from rational_onion.config import get_test_settings
        import copy
        
        # Get current settings
        settings = get_test_settings()
        original_api_keys = copy.deepcopy(settings.VALID_API_KEYS)
        
        try:
            # Step 1: Verify the current API key works
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
            assert response.status_code == 200, "Original API key should be valid"
            
            # Step 2: Generate a new API key and add it to valid keys
            new_api_key = "new_rotated_api_key_456"
            settings.VALID_API_KEYS = [new_api_key] + settings.VALID_API_KEYS
            
            # Step 3: Verify both keys work during transition period
            # Test original key
            response = test_client.post(
                "/insert-argument",
                headers={"X-API-Key": valid_api_key},
                json=test_data
            )
            assert response.status_code == 200, "Original API key should still be valid during transition"
            
            # Test new key
            response = test_client.post(
                "/insert-argument",
                headers={"X-API-Key": new_api_key},
                json=test_data
            )
            assert response.status_code == 200, "New API key should be valid"
            
            # Step 4: Remove the old key (complete rotation)
            settings.VALID_API_KEYS = [new_api_key]
            
            # Step 5: Verify old key no longer works
            response = test_client.post(
                "/insert-argument",
                headers={"X-API-Key": valid_api_key},
                json=test_data
            )
            assert response.status_code == 401, "Original API key should be invalid after rotation"
            
            # Step 6: Verify new key still works
            response = test_client.post(
                "/insert-argument",
                headers={"X-API-Key": new_api_key},
                json=test_data
            )
            assert response.status_code == 200, "New API key should still be valid after rotation"
            
        finally:
            # Restore original API keys
            settings.VALID_API_KEYS = original_api_keys

    query = """
    CREATE (a:Argument {claim: $claim})
    RETURN elementId(a) as argument_id
    """ 
from typing import Dict
from pydantic import BaseSettings
from functools import lru_cache

class TestSettings(BaseSettings):
    """Test configuration settings"""
    NEO4J_TEST_URI: str = "bolt://localhost:7687"
    NEO4J_TEST_USER: str = "neo4j"
    NEO4J_TEST_PASSWORD: str = "password"
    REDIS_TEST_HOST: str = "localhost"
    REDIS_TEST_PORT: int = 6379
    TEST_API_KEY: str = "test_key"
    RATE_LIMIT: str = "5/minute"
    
    # Test data configurations
    DEFAULT_TEST_ARGUMENT: Dict = {
        "claim": "Test claim",
        "grounds": "Test grounds",
        "warrant": "Test warrant"
    }
    
    # Error testing configurations
    TEST_ERROR_MESSAGES: Dict[str, str] = {
        "database": "Database operation failed",
        "validation": "Invalid argument structure",
        "graph": "Invalid graph structure",
        "citation": "Citation verification failed"
    }
    
    TEST_ERROR_DETAILS: Dict[str, Dict] = {
        "database": {"operation": "test_operation"},
        "validation": {"field": "test_field"},
        "graph": {"node": "test_node"},
        "citation": {"source": "test_source"}
    }
    
    class Config:
        env_file = ".env.test"

@lru_cache()
def get_test_settings() -> TestSettings:
    return TestSettings() 
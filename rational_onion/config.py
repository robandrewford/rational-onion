from typing import Dict, Any, List
from pydantic import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Base configuration settings"""
    # API Settings
    API_HOST: str = "localhost"
    API_PORT: int = 8000
    DEBUG: bool = False
    API_VERSION: str = "1.0.0"
    
    # Database Settings
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    NEO4J_DATABASE: str = "neo4j"  # Default Neo4j database name
    NEO4J_MAX_CONNECTION_POOL_SIZE: int = 50
    NEO4J_CONNECTION_TIMEOUT: int = 30
    NEO4J_ENCRYPTION_ENABLED: bool = False
    
    # Redis Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0  # Default Redis database number
    REDIS_SSL: bool = False  # SSL/TLS connection to Redis
    
    # NLP Service Settings
    SPACY_MODEL: str = "en_core_web_md"  # Default Spacy model
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"  # Default sentence transformer model
    
    # Security Settings
    API_KEY_NAME: str = "X-API-Key"
    VALID_API_KEYS: List[str] = ["test_api_key_123"]
    RATE_LIMIT: str = "100/minute"
    
    # Argument Settings
    MAX_CLAIM_LENGTH: int = 500
    MAX_GROUNDS_LENGTH: int = 1000
    MAX_WARRANT_LENGTH: int = 500
    
    # Cache Settings
    CACHE_TTL: int = 3600  # 1 hour
    CACHE_ENABLED: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

class TestSettings(Settings):
    """Test-specific settings"""
    DEBUG: bool = True
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    NEO4J_DATABASE: str = "neo4j"  # Default Neo4j database name for tests
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 1  # Use a different Redis database for tests
    REDIS_SSL: bool = False  # SSL/TLS for Redis in test environment
    SPACY_MODEL: str = "en_core_web_sm"  # Smaller Spacy model for tests
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"  # Same transformer model for tests
    TEST_API_KEY: str = "test_key"
    RATE_LIMIT: str = "5/minute"
    
    # Test Data
    DEFAULT_TEST_ARGUMENT: Dict[str, str] = {
        "claim": "Test Claim",
        "grounds": "Test Grounds",
        "warrant": "Test Warrant"
    }
    
    # Error Test Data
    TEST_ERROR_MESSAGES: Dict[str, str] = {
        "database": "Database operation failed",
        "validation": "Invalid argument structure",
        "graph": "Invalid graph structure",
        "citation": "Citation verification failed"
    }

    class Config:
        env_file = ".env.test"

@lru_cache()
def get_settings() -> Settings:
    """Get cached production settings"""
    return Settings()

@lru_cache()
def get_test_settings() -> TestSettings:
    """Get cached test settings"""
    return TestSettings(
        NEO4J_URI="bolt://localhost:7687",
        NEO4J_USER="neo4j",
        NEO4J_PASSWORD="password",
        NEO4J_DATABASE="neo4j",
        REDIS_DB=1,
        REDIS_SSL=False,
        SPACY_MODEL="en_core_web_sm",
        SENTENCE_TRANSFORMER_MODEL="all-MiniLM-L6-v2",
        VALID_API_KEYS=["test_api_key_123"],
        DEFAULT_TEST_ARGUMENT={
            "claim": "Test Claim",
            "grounds": "Test Grounds",
            "warrant": "Test Warrant"
        }
    ) 
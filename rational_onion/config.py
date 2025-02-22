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
    
    # Redis Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    
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
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
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
        VALID_API_KEYS=["test_api_key_123"]
    ) 
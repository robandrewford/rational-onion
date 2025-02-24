from typing import Dict, Any, List, Optional
from pydantic import BaseSettings, validator, conint, constr
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
    NEO4J_CONNECTION_TIMEOUT: int = 20
    NEO4J_ENCRYPTION_ENABLED: bool = True
    
    # Redis Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0  # Production uses DB 0
    REDIS_SSL: bool = False
    REDIS_PASSWORD: Optional[str] = None
    
    # NLP Settings
    SPACY_MODEL: str = "en_core_web_md"  # Production uses larger model
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"
    
    # Security Settings
    API_KEY_NAME: str = "X-API-Key"
    VALID_API_KEYS: List[str] = ["test_api_key_123"]
    RATE_LIMIT: str = "100/minute"
    
    # Argument Settings
    MAX_CLAIM_LENGTH: conint(gt=0) = 500
    MAX_GROUNDS_LENGTH: conint(gt=0) = 1000
    MAX_WARRANT_LENGTH: conint(gt=0) = 500
    
    # Cache Settings
    CACHE_TTL: int = 3600  # 1 hour
    CACHE_ENABLED: bool = True

    @validator("API_PORT")
    def validate_api_port(cls, v: int) -> int:
        """Validate API port number"""
        if v <= 0:
            raise ValueError("API port must be positive")
        return v
        
    @validator("REDIS_DB")
    def validate_redis_db(cls, v: int) -> int:
        """Validate Redis DB number"""
        if v < 0:
            raise ValueError("Redis DB must be non-negative")
        return v

    @validator("RATE_LIMIT")
    def validate_rate_limit(cls, v: str) -> str:
        """Validate rate limit format"""
        try:
            count, period = v.split("/")
            count = int(count)
            if count <= 0:
                raise ValueError("Rate limit count must be positive")
            if period not in ["second", "minute", "hour", "day"]:
                raise ValueError("Invalid rate limit period")
        except ValueError as e:
            raise ValueError(f"Invalid rate limit format: {e}")
        return v

    @validator("NEO4J_URI")
    def validate_neo4j_uri(cls, v: str) -> str:
        """Validate Neo4j URI format"""
        if not v.startswith(("bolt://", "neo4j://", "neo4j+s://")):
            raise ValueError("Invalid Neo4j URI scheme")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

class TestSettings(Settings):
    """Test-specific settings"""
    # Test environment specific settings
    DEBUG: bool = True
    REDIS_DB: int = 1  # Test environment uses DB 1
    NEO4J_ENCRYPTION_ENABLED: bool = False
    SPACY_MODEL: str = "en_core_web_sm"  # Smaller Spacy model for tests
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DEBUG = True  # Ensure DEBUG is always True in test settings
        self.REDIS_DB = 1  # Ensure REDIS_DB is always 1 in test settings
        self.NEO4J_CONNECTION_TIMEOUT = 30  # Ensure timeout is 30 in test settings
        self.NEO4J_ENCRYPTION_ENABLED = False  # Ensure encryption is disabled in test settings
        self.SPACY_MODEL = "en_core_web_sm"  # Ensure smaller model in test settings

    # Test data configurations
    DEFAULT_TEST_ARGUMENT: Dict[str, str] = {
        "claim": "Test Claim",
        "grounds": "Test Grounds",
        "warrant": "Test Warrant"
    }
    
    # Error testing configurations
    TEST_ERROR_MESSAGES: Dict[str, str] = {
        "database": "Database connection error",
        "validation": "Validation error",
        "graph": "Graph structure error",
        "citation": "Citation verification error"
    }

    # Disable rate limiting by default for tests

@lru_cache()
def get_settings() -> Settings:
    """Get cached production settings"""
    try:
        return Settings()
    except Exception as e:
        raise RuntimeError(f"Failed to load settings: {e}")

@lru_cache()
def get_test_settings() -> TestSettings:
    """Get cached test settings"""
    try:
        return TestSettings()
    except Exception as e:
        raise RuntimeError(f"Failed to load test settings: {e}") 
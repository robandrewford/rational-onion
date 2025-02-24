from typing import Dict
import os
import pytest
from rational_onion.config import Settings, TestSettings, get_settings, get_test_settings

def test_production_settings_values() -> None:
    """Test that production settings have expected values"""
    settings = get_settings()
    # API Settings
    assert settings.API_HOST == "localhost"
    assert settings.API_PORT == 8000
    assert isinstance(settings.DEBUG, bool)
    assert settings.API_VERSION == "1.0.0"
    
    # Database Settings
    assert settings.NEO4J_URI == "bolt://localhost:7687"
    assert settings.NEO4J_USER == "neo4j"
    assert settings.NEO4J_PASSWORD == "password"
    assert settings.NEO4J_DATABASE == "neo4j"
    assert settings.NEO4J_MAX_CONNECTION_POOL_SIZE == 50
    assert settings.NEO4J_CONNECTION_TIMEOUT == 30
    assert settings.NEO4J_ENCRYPTION_ENABLED is False
    
    # Redis Settings
    assert settings.REDIS_HOST == "localhost"
    assert settings.REDIS_PORT == 6379
    assert settings.REDIS_PASSWORD == ""
    assert settings.REDIS_DB == 0
    assert settings.REDIS_SSL is False
    
    # NLP Service Settings
    assert settings.SPACY_MODEL == "en_core_web_md"
    assert settings.SENTENCE_TRANSFORMER_MODEL == "all-MiniLM-L6-v2"
    
    # Security Settings
    assert settings.API_KEY_NAME == "X-API-Key"
    assert settings.VALID_API_KEYS == ["test_api_key_123"]
    assert settings.RATE_LIMIT == "100/minute"
    
    # Argument Settings
    assert settings.MAX_CLAIM_LENGTH == 500
    assert settings.MAX_GROUNDS_LENGTH == 1000
    assert settings.MAX_WARRANT_LENGTH == 500
    
    # Cache Settings
    assert settings.CACHE_TTL == 3600
    assert settings.CACHE_ENABLED is True

def test_test_settings_values() -> None:
    """Test that test settings have expected values"""
    settings = get_test_settings()
    # Test environment specific settings
    assert settings.DEBUG is True
    assert settings.NEO4J_URI == "bolt://localhost:7687"
    assert settings.NEO4J_USER == "neo4j"
    assert settings.NEO4J_PASSWORD == "password"
    assert settings.NEO4J_DATABASE == "neo4j"
    assert settings.NEO4J_MAX_CONNECTION_POOL_SIZE == 50
    assert settings.NEO4J_CONNECTION_TIMEOUT == 30
    assert settings.NEO4J_ENCRYPTION_ENABLED is False
    
    assert settings.REDIS_HOST == "localhost"
    assert settings.REDIS_PORT == 6379
    assert settings.REDIS_DB == 1  # Different from production
    assert settings.REDIS_SSL is False
    
    assert settings.SPACY_MODEL == "en_core_web_sm"  # Different from production
    assert settings.SENTENCE_TRANSFORMER_MODEL == "all-MiniLM-L6-v2"
    
    assert settings.RATE_LIMIT == "100/minute"
    assert settings.VALID_API_KEYS == ["test_api_key_123"]
    
    # Test data configurations
    assert isinstance(settings.DEFAULT_TEST_ARGUMENT, dict)
    assert "claim" in settings.DEFAULT_TEST_ARGUMENT
    assert "grounds" in settings.DEFAULT_TEST_ARGUMENT
    assert "warrant" in settings.DEFAULT_TEST_ARGUMENT
    
    # Error testing configurations
    assert isinstance(settings.TEST_ERROR_MESSAGES, dict)
    assert "database" in settings.TEST_ERROR_MESSAGES
    assert "validation" in settings.TEST_ERROR_MESSAGES
    assert "graph" in settings.TEST_ERROR_MESSAGES
    assert "citation" in settings.TEST_ERROR_MESSAGES

def test_settings_env_override() -> None:
    """Test that environment variables override default settings"""
    # Set test environment variables
    os.environ["API_HOST"] = "test.host"
    os.environ["API_PORT"] = "9000"
    os.environ["NEO4J_URI"] = "bolt://test.neo4j:7687"
    os.environ["REDIS_HOST"] = "test.redis"
    
    # Get fresh settings instance
    settings = Settings()
    
    # Check overrides worked
    assert settings.API_HOST == "test.host"
    assert settings.API_PORT == 9000
    assert settings.NEO4J_URI == "bolt://test.neo4j:7687"
    assert settings.REDIS_HOST == "test.redis"
    
    # Clean up
    del os.environ["API_HOST"]
    del os.environ["API_PORT"]
    del os.environ["NEO4J_URI"]
    del os.environ["REDIS_HOST"]

def test_settings_cache() -> None:
    """Test that settings are properly cached"""
    # Get settings instances
    settings1 = get_settings()
    settings2 = get_settings()
    test_settings1 = get_test_settings()
    test_settings2 = get_test_settings()
    
    # Check that cached instances are the same object
    assert settings1 is settings2
    assert test_settings1 is test_settings2
    
    # Check that production and test settings are different objects
    assert settings1 is not test_settings1

def test_settings_validation() -> None:
    """Test settings validation"""
    # Test invalid port number
    with pytest.raises(ValueError):
        Settings(API_PORT=-1)
    
    # Test invalid max lengths
    with pytest.raises(ValueError):
        Settings(MAX_CLAIM_LENGTH=0)
    
    # Test invalid Redis DB
    with pytest.raises(ValueError):
        Settings(REDIS_DB=-1)
        
    # Test invalid rate limit format
    with pytest.raises(ValueError):
        Settings(RATE_LIMIT="invalid")
    with pytest.raises(ValueError):
        Settings(RATE_LIMIT="0/minute")
    with pytest.raises(ValueError):
        Settings(RATE_LIMIT="100/invalid")
        
    # Test invalid Neo4j URI format
    with pytest.raises(ValueError):
        Settings(NEO4J_URI="invalid://localhost:7687")
    with pytest.raises(ValueError):
        Settings(NEO4J_URI="http://localhost:7687")

def test_settings_env_override_extended() -> None:
    """Test extended environment variable override scenarios"""
    # Test boolean overrides
    os.environ["DEBUG"] = "true"
    os.environ["REDIS_SSL"] = "true"
    os.environ["CACHE_ENABLED"] = "false"
    
    settings = Settings()
    assert settings.DEBUG is True
    assert settings.REDIS_SSL is True
    assert settings.CACHE_ENABLED is False
    
    # Test numeric overrides
    os.environ["CACHE_TTL"] = "7200"
    os.environ["MAX_CLAIM_LENGTH"] = "1000"
    settings = Settings()
    assert settings.CACHE_TTL == 7200
    assert settings.MAX_CLAIM_LENGTH == 1000
    
    # Test list override
    os.environ["VALID_API_KEYS"] = '["key1", "key2"]'
    settings = Settings()
    assert settings.VALID_API_KEYS == ["key1", "key2"]
    
    # Clean up
    del os.environ["DEBUG"]
    del os.environ["REDIS_SSL"]
    del os.environ["CACHE_ENABLED"]
    del os.environ["CACHE_TTL"]
    del os.environ["MAX_CLAIM_LENGTH"]
    del os.environ["VALID_API_KEYS"]

def test_config_class_settings() -> None:
    """Test Config class settings"""
    settings = Settings()
    assert settings.__config__.env_file == ".env"
    assert settings.__config__.env_file_encoding == "utf-8"
    assert settings.__config__.case_sensitive is True

def test_test_settings_inheritance() -> None:
    """Test that TestSettings properly inherits and overrides Settings"""
    prod_settings = Settings()
    test_settings = TestSettings()
    
    # Check that TestSettings overrides specific values
    assert test_settings.DEBUG != prod_settings.DEBUG
    assert test_settings.REDIS_DB != prod_settings.REDIS_DB
    assert test_settings.SPACY_MODEL != prod_settings.SPACY_MODEL
    
    # Check that non-overridden values remain the same
    assert test_settings.API_VERSION == prod_settings.API_VERSION
    assert test_settings.NEO4J_MAX_CONNECTION_POOL_SIZE == prod_settings.NEO4J_MAX_CONNECTION_POOL_SIZE
    assert test_settings.SENTENCE_TRANSFORMER_MODEL == prod_settings.SENTENCE_TRANSFORMER_MODEL 

def test_test_settings_data_configurations() -> None:
    """Test the test data configurations in TestSettings"""
    settings = TestSettings()
    
    # Test default argument structure
    assert isinstance(settings.DEFAULT_TEST_ARGUMENT, dict)
    assert all(key in settings.DEFAULT_TEST_ARGUMENT for key in ["claim", "grounds", "warrant"])
    assert all(isinstance(value, str) for value in settings.DEFAULT_TEST_ARGUMENT.values())
    
    # Test error messages structure
    assert isinstance(settings.TEST_ERROR_MESSAGES, dict)
    error_categories = ["database", "validation", "graph", "citation"]
    assert all(category in settings.TEST_ERROR_MESSAGES for category in error_categories)
    assert all(isinstance(settings.TEST_ERROR_MESSAGES[cat], str) for cat in error_categories)

def test_settings_type_validation() -> None:
    """Test type validation for settings fields"""
    # Test invalid types for numeric fields
    with pytest.raises(ValueError):
        Settings(API_PORT="invalid")
    with pytest.raises(ValueError):
        Settings(CACHE_TTL="invalid")
    with pytest.raises(ValueError):
        Settings(MAX_CLAIM_LENGTH="invalid")
        
    # Test invalid types for boolean fields
    with pytest.raises(ValueError):
        Settings(DEBUG="not_a_bool")
    with pytest.raises(ValueError):
        Settings(REDIS_SSL="not_a_bool")
        
    # Test invalid types for list fields
    with pytest.raises(ValueError):
        Settings(VALID_API_KEYS="not_a_list") 
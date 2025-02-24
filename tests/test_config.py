from typing import Dict
from rational_onion.config import TestSettings, get_test_settings

def test_settings_values() -> None:
    """Test that test settings have expected values"""
    settings = get_test_settings()
    assert settings.NEO4J_URI == "bolt://localhost:7687"
    assert settings.NEO4J_USER == "neo4j"
    assert settings.NEO4J_PASSWORD == "password"
    assert settings.REDIS_HOST == "localhost"
    assert settings.REDIS_PORT == 6379
    assert settings.VALID_API_KEYS == ["test_api_key_123"]
    assert settings.RATE_LIMIT == "100/minute"
    
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
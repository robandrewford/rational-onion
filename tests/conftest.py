import logging
import socket
import asyncio
from typing import AsyncGenerator, Generator, Callable, Any
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from redis import Redis
import pytest
import pytest_asyncio
from rational_onion.config import TestSettings, get_test_settings
from fastapi.testclient import TestClient
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

settings = get_test_settings()

def get_test_connection_resolver() -> Callable[[tuple | str], list[tuple[str, int]]]:
    """Custom resolver to force IPv4 for tests"""
    def resolve(address: tuple | str) -> list[tuple[str, int]]:
        if isinstance(address, tuple):
            host, port = address
        else:
            host, port = address.partition(':')[::2]
            port = int(port) if port else 7687
        return [(str(host), port)]
    return resolve

@pytest.fixture(scope="function")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for each test."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    # Clean up all pending tasks
    pending = asyncio.all_tasks(loop)
    for task in pending:
        task.cancel()
    # Run loop to complete any remaining tasks
    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def neo4j_test_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test Neo4j session."""
    driver = AsyncGraphDatabase.driver(
        "bolt://127.0.0.1:7687",
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        max_connection_lifetime=60,
        max_connection_pool_size=1,
        connection_timeout=5,
        encrypted=False
    )
    
    try:
        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            # Clear existing data
            await session.run("MATCH (n) DETACH DELETE n")
            yield session
    finally:
        await driver.close()

@pytest.fixture(scope="session")
def redis_test_client() -> Generator[Redis, None, None]:
    """Create a test Redis client."""
    log.debug("Creating Redis test client")
    client = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True
    )
    
    try:
        # Verify Redis connection
        client.ping()
        log.debug("Successfully verified Redis connection")
    except Exception as e:
        log.error(f"Failed to verify Redis connection: {e}")
        client.close()
        raise

    try:
        yield client
    finally:
        log.debug("Closing Redis test client")
        client.close()

@pytest.fixture(scope="function")
def disable_rate_limit() -> Generator[None, None, None]:
    """Disable rate limiting for tests."""
    class MockLimiter:
        def __init__(self) -> None:
            self.enabled = True
            
        def __call__(self, *args: Any, **kwargs: Any) -> Callable[[Any], Any]:
            return lambda func: func

    try:
        from rational_onion.api.rate_limiting import limiter
    except (ImportError, ModuleNotFoundError):
        log.warning("Could not import rate limiting module. Using mock limiter.")
        limiter = limiter.__class__(key_func=lambda x: x, enabled=True)  # type: ignore

    previous_state = limiter.enabled
    limiter.enabled = False
    yield
    limiter.enabled = previous_state

@pytest.fixture(scope="session")
def valid_api_key() -> str:
    """Provide a valid API key for testing."""
    return settings.TEST_API_KEY

@pytest.fixture(scope="session")
def test_client() -> TestClient:
    """Create a test client for the FastAPI application."""
    from rational_onion.api.main import app
    return TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def configure_test_env() -> None:
    """Configure test environment settings"""
    from rational_onion.api.dependencies import limiter
    # Disable rate limiting by default for tests
    limiter.enabled = False
    
    # Ensure test database is used
    settings = get_test_settings()
    os.environ["NEO4J_DATABASE"] = settings.NEO4J_DATABASE
    os.environ["REDIS_DB"] = str(settings.REDIS_DB)

@pytest.fixture(autouse=True)
async def cleanup_test_data(neo4j_test_session: AsyncSession) -> AsyncGenerator[None, None]:
    """Clean up test data before and after each test"""
    await neo4j_test_session.run("MATCH (n) DETACH DELETE n")
    yield 
import logging
import socket
import asyncio
from typing import AsyncGenerator, Generator, Callable, Any
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from redis import Redis
import pytest
import pytest_asyncio
from rational_onion.config import TestSettings
from fastapi.testclient import TestClient

# Configure logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

settings = TestSettings()

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

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def neo4j_test_driver() -> AsyncGenerator[AsyncDriver, None]:
    """Create a test Neo4j driver instance."""
    log.debug("Creating Neo4j test driver")
    
    # Create driver with explicit IPv4 address and additional parameters
    driver = AsyncGraphDatabase.driver(
        "bolt://127.0.0.1:7687",
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        max_connection_lifetime=60,  # 1 minute max lifetime
        max_connection_pool_size=1,  # Limit pool size for tests
        connection_timeout=5,  # 5 seconds timeout
        encrypted=False  # Disable encryption for local testing
    )

    try:
        # Verify the connection works
        async with driver.session() as session:
            result = await session.run("RETURN 1")
            await result.consume()
            log.debug("Successfully verified Neo4j connection")
    except Exception as e:
        log.error(f"Failed to verify Neo4j connection: {e}")
        await driver.close()
        raise

    try:
        yield driver
    finally:
        log.debug("Closing Neo4j test driver")
        await driver.close()

@pytest_asyncio.fixture(scope="session")
async def neo4j_test_session(neo4j_test_driver: AsyncDriver) -> AsyncGenerator[AsyncSession, None]:
    """Create a test Neo4j session."""
    log.debug("Creating Neo4j test session")
    session = neo4j_test_driver.session()
    
    try:
        # Clear existing data
        await session.run("MATCH (n) DETACH DELETE n")
        log.debug("Cleared existing Neo4j data")
        
        yield session
    finally:
        log.debug("Closing Neo4j test session")
        await session.close()

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
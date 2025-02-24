# rational_onion/services/neo4j_service.py

from neo4j import AsyncGraphDatabase
from rational_onion.config import get_settings
import logging
import socket
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

settings = get_settings()

def get_connection_resolver():
    """Custom resolver to force IPv4"""
    def resolve(address):
        host, port = address.partition(':')[::2]
        port = int(port) if port else 7687
        return [('127.0.0.1', port)]
    return resolve

# Initialize Neo4j driver with improved connection handling
driver = AsyncGraphDatabase.driver(
    "bolt://127.0.0.1:7687",  # Force IPv4 address
    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
    max_connection_lifetime=60,  # 1 minute max lifetime
    max_connection_pool_size=settings.NEO4J_MAX_CONNECTION_POOL_SIZE,
    connection_timeout=settings.NEO4J_CONNECTION_TIMEOUT,
    encrypted=settings.NEO4J_ENCRYPTION_ENABLED,
    resolver=get_connection_resolver()  # Use custom resolver
)

# Export driver for use in other modules
__all__ = ['driver']

async def get_argument_by_id(self, argument_id: int) -> Dict[str, Any]:
    query = """
    MATCH (a:Argument)
    WHERE elementId(a) = $argument_id
    RETURN a
    """
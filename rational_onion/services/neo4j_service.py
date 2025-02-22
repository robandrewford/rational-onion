# rational_onion/services/neo4j_service.py

from neo4j import AsyncGraphDatabase
from rational_onion.config import get_settings

settings = get_settings()

driver = AsyncGraphDatabase.driver(
    settings.NEO4J_URI,
    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
    database=settings.NEO4J_DATABASE,
    max_connection_pool_size=settings.NEO4J_MAX_CONNECTION_POOL_SIZE,
    connection_timeout=settings.NEO4J_CONNECTION_TIMEOUT,
    encrypted=settings.NEO4J_ENCRYPTION_ENABLED
)
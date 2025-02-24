from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, ClientError, DatabaseError
import pytest
import logging
import asyncio
from typing import Optional, AsyncGenerator
from rational_onion.config import get_test_settings

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
settings = get_test_settings()

class TestNeo4jConnection:
    """Test suite for Neo4j connection handling"""

    def test_basic_connection(self) -> None:
        """Test basic Neo4j connection"""
        try:
            driver = GraphDatabase.driver(
                'bolt://127.0.0.1:7687',
                auth=('neo4j', 'password'),
                connection_timeout=5
            )
            
            with driver.session() as session:
                result = session.run('RETURN 1 as n')
                record = result.single()
                assert record and record['n'] == 1
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise
        finally:
            driver.close()

    def test_connection_pool(self) -> None:
        """Test Neo4j connection pool behavior"""
        driver = GraphDatabase.driver(
            'bolt://127.0.0.1:7687',
            auth=('neo4j', 'password'),
            max_connection_pool_size=settings.NEO4J_MAX_CONNECTION_POOL_SIZE,
            connection_timeout=settings.NEO4J_CONNECTION_TIMEOUT
        )
        
        try:
            # Test multiple concurrent sessions
            sessions = []
            for _ in range(5):
                session = driver.session()
                result = session.run('RETURN 1')
                assert result.single()
                sessions.append(session)
            
            # Clean up sessions
            for session in sessions:
                session.close()
                
        finally:
            driver.close()

    def test_connection_timeout(self) -> None:
        """Test connection timeout handling"""
        with pytest.raises(ServiceUnavailable):
            driver = GraphDatabase.driver(
                'bolt://10.255.255.1:7687',  # Use a non-routable IP address
                auth=('neo4j', 'password'),
                connection_timeout=1
            )
            with driver.session() as session:
                session.run('RETURN 1')

    def test_authentication_error(self) -> None:
        """Test authentication error handling"""
        with pytest.raises(ClientError):
            driver = GraphDatabase.driver(
                'bolt://127.0.0.1:7687',
                auth=('neo4j', 'wrong_password'),
                connection_timeout=5
            )
            with driver.session() as session:
                session.run('RETURN 1')

    def test_connection_recovery(self) -> None:
        """Test connection recovery after failure"""
        driver = GraphDatabase.driver(
            'bolt://127.0.0.1:7687',
            auth=('neo4j', 'password'),
            connection_timeout=5
        )
        
        try:
            # First query should succeed
            with driver.session() as session:
                result = session.run('RETURN 1')
                assert result.single()
            
            # Force connection error by closing driver
            driver.close()
            
            # Reconnect and try again
            driver = GraphDatabase.driver(
                'bolt://127.0.0.1:7687',
                auth=('neo4j', 'password'),
                connection_timeout=5
            )
            
            with driver.session() as session:
                result = session.run('RETURN 1')
                assert result.single()
                
        finally:
            driver.close()

    def test_database_error_handling(self) -> None:
        """Test handling of database errors"""
        driver = GraphDatabase.driver(
            'bolt://127.0.0.1:7687',
            auth=('neo4j', 'password'),
            connection_timeout=5
        )
        
        try:
            with driver.session() as session:
                # Test invalid Cypher query
                with pytest.raises(ClientError):
                    session.run('INVALID QUERY')
                
                # Test valid query after error
                result = session.run('RETURN 1')
                assert result.single()
        finally:
            driver.close()

if __name__ == "__main__":
    pytest.main([__file__]) 
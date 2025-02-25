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
        driver = None
        try:
            with pytest.raises(ServiceUnavailable):
                driver = GraphDatabase.driver(
                    'bolt://10.255.255.1:7687',  # Use a non-routable IP address
                    auth=('neo4j', 'password'),
                    connection_timeout=1
                )
                with driver.session() as session:
                    session.run('RETURN 1')
        finally:
            if driver:
                driver.close()

    def test_authentication_error(self) -> None:
        """Test authentication error handling"""
        driver = None
        try:
            with pytest.raises(ClientError):
                driver = GraphDatabase.driver(
                    'bolt://127.0.0.1:7687',
                    auth=('neo4j', 'wrong_password'),
                    connection_timeout=5
                )
                with driver.session() as session:
                    session.run('RETURN 1')
        finally:
            if driver:
                driver.close()

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

    def test_connection_pool_stress(self) -> None:
        """Test Neo4j connection pool under stress"""
        driver = GraphDatabase.driver(
            'bolt://127.0.0.1:7687',
            auth=('neo4j', 'password'),
            max_connection_pool_size=settings.NEO4J_MAX_CONNECTION_POOL_SIZE,
            connection_timeout=settings.NEO4J_CONNECTION_TIMEOUT
        )
        
        try:
            # Run multiple queries in parallel to stress the connection pool
            from concurrent.futures import ThreadPoolExecutor
            
            def run_query(i):
                with driver.session() as session:
                    result = session.run('RETURN $i as n', {'i': i})
                    record = result.single()
                    assert record and record['n'] == i
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                list(executor.map(run_query, range(20)))
                
        finally:
            driver.close()
            
    def test_transaction_handling(self) -> None:
        """Test explicit transaction handling"""
        driver = GraphDatabase.driver(
            'bolt://127.0.0.1:7687',
            auth=('neo4j', 'password'),
            connection_timeout=5
        )
        
        try:
            # Create test data
            with driver.session() as session:
                session.run("CREATE (n:TestNode {name: 'test'}) RETURN n")
            
            # Test successful transaction
            with driver.session() as session:
                tx = session.begin_transaction()
                try:
                    tx.run("MATCH (n:TestNode {name: 'test'}) SET n.value = 'updated'")
                    tx.commit()
                except Exception:
                    tx.rollback()
                    raise
            
            # Verify update
            with driver.session() as session:
                result = session.run("MATCH (n:TestNode {name: 'test'}) RETURN n.value")
                record = result.single()
                assert record and record['n.value'] == 'updated'
                
            # Test transaction rollback
            with driver.session() as session:
                tx = session.begin_transaction()
                try:
                    tx.run("MATCH (n:TestNode {name: 'test'}) SET n.value = 'should_not_persist'")
                    # Simulate an error
                    raise ValueError("Simulated error")
                    tx.commit()
                except Exception:
                    tx.rollback()
            
            # Verify rollback (value should still be 'updated')
            with driver.session() as session:
                result = session.run("MATCH (n:TestNode {name: 'test'}) RETURN n.value")
                record = result.single()
                assert record and record['n.value'] == 'updated'
                
        finally:
            # Clean up
            with driver.session() as session:
                session.run("MATCH (n:TestNode) DETACH DELETE n")
            driver.close()
            
    def test_database_selection(self) -> None:
        """Test connecting to different databases"""
        driver = GraphDatabase.driver(
            'bolt://127.0.0.1:7687',
            auth=('neo4j', 'password'),
            connection_timeout=5
        )
        
        try:
            # Test default database
            with driver.session() as session:
                result = session.run("CALL db.info()")
                record = result.single()
                assert record is not None
                
            # Test system database
            with driver.session(database="system") as session:
                result = session.run("SHOW DATABASES")
                records = list(result)
                assert len(records) > 0
                
        finally:
            driver.close()
            
    def test_connection_retry(self) -> None:
        """Test connection retry after temporary failure"""
        from unittest.mock import patch
        
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
            
            # Mock a temporary connection failure
            original_acquire = driver._pool.acquire
            
            call_count = 0
            def mock_acquire(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise ServiceUnavailable("Simulated temporary failure")
                return original_acquire(*args, **kwargs)
            
            with patch.object(driver._pool, 'acquire', side_effect=mock_acquire):
                # This should fail with ServiceUnavailable
                with pytest.raises(ServiceUnavailable):
                    with driver.session() as session:
                        session.run('RETURN 1')
                
                # Second attempt should work
                with driver.session() as session:
                    result = session.run('RETURN 1')
                    assert result.single()
                    
        finally:
            driver.close()

if __name__ == "__main__":
    pytest.main([__file__]) 
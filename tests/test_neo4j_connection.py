from neo4j import GraphDatabase
import logging
from typing import Optional

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_neo4j_connection() -> None:
    try:
        driver = GraphDatabase.driver(
            'bolt://127.0.0.1:7687', 
            auth=('neo4j', 'password'),
            connection_timeout=5
        )
        
        with driver.session() as session:
            result = session.run('RETURN 1 as n')
            record = result.single()
            if record:
                print(f"Connection successful. Result: {record['n']}")
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        raise

if __name__ == "__main__":
    test_neo4j_connection() 
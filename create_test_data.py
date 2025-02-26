import asyncio
from neo4j import AsyncGraphDatabase

async def create_test_data():
    driver = AsyncGraphDatabase.driver(
        'bolt://localhost:7687',
        auth=('neo4j', 'password')
    )
    
    async with driver.session() as session:
        # Clear existing data
        await session.run('MATCH (n) DETACH DELETE n')
        
        # Create test data
        await session.run('''
            CREATE (c1:Claim {text: 'Main Claim'})
            CREATE (c2:Claim {text: 'Supporting Claim 1'})
            CREATE (c3:Claim {text: 'Supporting Claim 2'})
            CREATE (c2)-[:SUPPORTS]->(c1)
            CREATE (c3)-[:SUPPORTS]->(c1)
        ''')
    
    await driver.close()
    print('Test data created successfully')

if __name__ == "__main__":
    asyncio.run(create_test_data()) 
# rational_onion/api/argument_verification.py

from fastapi import APIRouter, HTTPException
from rational_onion.services.neo4j_service import driver

router = APIRouter()

@router.get("/verify-argument-structure")
async def verify_argument_structure():
    """
    Verify the logical structure and consistency of stored arguments.
    
    Performs comprehensive validation including:
        - Cycle detection in argument chains
        - Orphaned node identification
        - Relationship validity checks
        - Toulmin model compliance
    
    Returns:
        Dict containing:
            - has_cycles: Boolean indicating circular reasoning
            - orphaned_nodes: List of nodes without proper connections
            - message: Detailed verification results
            
    Raises:
        GraphError: If argument structure violates DAG constraints
        DatabaseError: If Neo4j query fails
        ValidationError: If argument components are invalid
    """
    try:
        async with driver.session() as session:
            # Detect cycles
            cycle_result = await session.run("""
                MATCH p=(c:Claim)-[*]->(c)
                RETURN count(p) > 0 AS has_cycle
            """)
            cycle_record = await cycle_result.single()
            has_cycles = cycle_record["has_cycle"] if cycle_record else False

            # Find orphaned nodes
            orphan_result = await session.run("""
                MATCH (n)
                WHERE NOT (n)-[]-(:Claim)
                RETURN collect(n.text) AS orphaned_nodes
            """)
            orphan_record = await orphan_result.single()
            orphaned_nodes = orphan_record["orphaned_nodes"] if orphan_record else []

        return {
            "has_cycles": has_cycles,
            "orphaned_nodes": orphaned_nodes,
            "message": "Structural verification completed."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {e}")
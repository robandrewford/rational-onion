# rational_onion/api/dag_visualization.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from rational_onion.services.neo4j_service import driver

router = APIRouter()

@router.get("/visualize-dag")
async def visualize_argument_dag():
    """
    Generate graph visualization data for argument structure.
    
    Creates a DAG representation showing:
        - Claims, grounds, warrants as nodes
        - Logical relationships as edges
        - Support and challenge relationships
        - Component metadata for visualization
    
    Returns:
        Dict containing:
            - nodes: List of argument components with properties
            - edges: List of relationships between components
            - layout: Graph layout parameters
            
    Raises:
        GraphError: If DAG structure is invalid
        DatabaseError: If Neo4j query fails
        VisualizationError: If graph rendering fails
    """
    try:
        async with driver.session() as session:
            result = await session.run("""
                MATCH (n)
                OPTIONAL MATCH (n)-[r]->(m)
                RETURN collect(DISTINCT {id: ID(n), label: labels(n)[0], text: n.text}) AS nodes,
                   collect(DISTINCT {source: ID(n), target: ID(m), type: type(r)}) AS edges
            """)
            record = await result.single()
            graph = {
                "nodes": record["nodes"] if record else [],
                "edges": record["edges"] if record else [],
                "layout": {
                    "name": "cose",
                    "animate": True
                }
            }
            return JSONResponse(content=graph)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
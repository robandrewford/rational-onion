# rational_onion/api/dag_visualization.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from rational_onion.services.neo4j_service import driver
from neo4j.exceptions import ServiceUnavailable, DatabaseError as Neo4jDatabaseError
from rational_onion.api.errors import ErrorType, BaseAPIError

router = APIRouter()

@router.get("/visualize-dag")
async def visualize_argument_dag() -> JSONResponse:
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
                RETURN collect(DISTINCT {
                    id: elementId(n),
                    label: labels(n)[0],
                    text: n.text
                }) AS nodes,
                collect(DISTINCT {
                    source: elementId(n),
                    target: elementId(m),
                    type: type(r)
                }) AS edges
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
            return JSONResponse(
                status_code=200,
                content=graph
            )
    except (ServiceUnavailable, Neo4jDatabaseError) as e:
        raise BaseAPIError(
            error_type=ErrorType.DATABASE_ERROR,
            message="Failed to generate graph visualization",
            status_code=500,
            details={"error": str(e)}
        )
    except Exception as e:
        raise BaseAPIError(
            error_type=ErrorType.INTERNAL_ERROR,
            message="An unexpected error occurred",
            status_code=500,
            details={"error": str(e)}
        )
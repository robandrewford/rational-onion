# rational_onion/api/dag_visualization.py

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from neo4j import AsyncSession
from neo4j.exceptions import ServiceUnavailable, DatabaseError as Neo4jDatabaseError
from rational_onion.api.errors import ErrorType, BaseAPIError
from rational_onion.api.dependencies import limiter, verify_api_key, get_db

router = APIRouter()

@router.get("/visualize-dag")
@limiter.limit("100/minute")
async def visualize_argument_dag(
    request: Request,
    session: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
) -> JSONResponse:
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
        result = await session.run("""
            MATCH (n:Claim)
            OPTIONAL MATCH (n)-[r]->(m:Claim)
            RETURN collect(DISTINCT {
                id: elementId(n),
                label: labels(n)[0],
                claim: n.claim,
                grounds: n.grounds,
                warrant: n.warrant
            }) AS nodes,
            collect(DISTINCT CASE WHEN m IS NOT NULL THEN {
                source: elementId(n),
                target: elementId(m),
                type: type(r)
            } END) AS edges
        """)
        record = await result.single()
        graph = {
            "nodes": record["nodes"] if record else [],
            "edges": [edge for edge in record["edges"] if edge is not None] if record else [],
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
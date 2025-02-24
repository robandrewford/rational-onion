# rational_onion/api/dag_visualization.py

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from neo4j import AsyncSession
from neo4j.exceptions import ServiceUnavailable, DatabaseError as Neo4jDatabaseError
from rational_onion.api.dependencies import limiter, get_db, verify_api_key
from rational_onion.api.errors import ErrorType
from typing import Dict, Any, List
from pydantic import BaseModel

router = APIRouter()

class DagVisualizationResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    layout: Dict[str, str] = {"name": "cose"}
    message: str = "Graph visualization generated successfully"

@router.get("/visualize-argument-dag")
@limiter.limit("100/minute")
async def visualize_argument_dag(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
) -> JSONResponse:
    """Generate a visualization of the argument DAG"""
    try:
        # Query to get all nodes and relationships
        query = """
        MATCH (n:Claim)
        OPTIONAL MATCH (n)-[r]->(m:Claim)
        RETURN collect(distinct n) as nodes, collect(distinct r) as edges
        """
        result = await session.run(query)
        record = await result.single()
        
        if not record:
            return JSONResponse(
                status_code=404,
                content={
                    "detail": {
                        "error_type": ErrorType.GRAPH_ERROR.value,
                        "message": "No data found for visualization"
                    }
                }
            )
        
        # Process nodes
        nodes = []
        for node in record["nodes"]:
            nodes.append({
                "id": str(node.element_id),
                "label": "Claim",
                "text": node["text"],
                "type": "claim"
            })
        
        # Process edges
        edges = []
        for edge in record["edges"]:
            edges.append({
                "source": str(edge.start_node.element_id),
                "target": str(edge.end_node.element_id),
                "type": edge.type
            })
        
        return JSONResponse(
            status_code=200,
            content=DagVisualizationResponse(
                nodes=nodes,
                edges=edges,
                layout={"name": "cose"},
                message="Graph visualization generated successfully"
            ).dict()
        )
        
    except (ServiceUnavailable, Neo4jDatabaseError) as e:
        return JSONResponse(
            status_code=500,
            content={
                "detail": {
                    "error_type": ErrorType.DATABASE_ERROR.value,
                    "message": str(e)
                }
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "detail": {
                    "error_type": ErrorType.INTERNAL_ERROR.value,
                    "message": "An unexpected error occurred"
                }
            }
        )
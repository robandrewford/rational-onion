# rational_onion/api/dag_visualization.py

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from neo4j import AsyncSession
from neo4j.exceptions import ServiceUnavailable, DatabaseError as Neo4jDatabaseError
from rational_onion.api.dependencies import limiter, get_db, verify_api_key
from rational_onion.api.errors import ErrorType
from typing import Dict, Any, List
from pydantic import BaseModel
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

class DagVisualizationResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    layout: Dict[str, Any] = {"name": "cose"}
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
        logger.info("Processing visualization request")
        
        # Add more detailed logging
        logger.info(f"Visualization request received - Method: {request.method}, Headers: {dict(request.headers)}")
        
        # Log API key validation
        logger.info(f"API Key validation - Key provided: {bool(api_key)}")
        
        # Add more detailed CORS logging
        logger.info(f"CORS Headers - Origin: {request.headers.get('Origin', 'Not Set')}, Referer: {request.headers.get('Referer', 'Not Set')}")
        
        # Add CORS headers with more explicit logging
        logger.info("Setting CORS headers explicitly")
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key"
        response.headers["Access-Control-Expose-Headers"] = "*"
        
        # Log the client's IP address for debugging
        client_host = request.client.host if request.client else "Unknown"
        logger.info(f"Request from client IP: {client_host}")
        
        # Query to get all nodes and relationships
        query = """
        MATCH (n:Claim)
        OPTIONAL MATCH (n)-[r]->(m)
        WHERE m:Claim
        RETURN collect(distinct n) as nodes, collect(distinct r) as edges
        """
        result = await session.run(query)
        record = await result.single()
        
        if not record:
            logger.warning("No data found for visualization")
            # Return empty arrays instead of error
            return JSONResponse(
                status_code=200,
                content=DagVisualizationResponse(
                    nodes=[],
                    edges=[],
                    layout={"name": "cose"},
                    message="No data found for visualization"
                ).dict()
            )
        
        # Process nodes
        nodes = []
        for node in record["nodes"]:
            node_data = {
                "id": str(node.element_id),
                "label": "Claim",
                "text": node.get("text", "Unnamed Claim"),
                "type": "claim",
                "details": node.get("details", "")
            }
            nodes.append(node_data)
            logger.debug(f"Added node: {node_data}")
        
        # Process edges
        edges = []
        for edge in record["edges"]:
            edge_data = {
                "source": str(edge.start_node.element_id),
                "target": str(edge.end_node.element_id),
                "type": edge.type
            }
            edges.append(edge_data)
            logger.debug(f"Added edge: {edge_data}")
        
        logger.info(f"Returning visualization with {len(nodes)} nodes and {len(edges)} edges")
        
        return JSONResponse(
            status_code=200,
            content=DagVisualizationResponse(
                nodes=nodes,
                edges=edges,
                layout={
                    "name": "cose",
                    "nodeDimensionsIncludeLabels": True,
                    "refresh": 20,
                    "fit": True,
                    "padding": 30,
                    "randomize": False,
                    "componentSpacing": 100,
                    "nodeRepulsion": 400000,
                    "nodeOverlap": 10,
                    "idealEdgeLength": 100,
                    "edgeElasticity": 100,
                    "nestingFactor": 5,
                    "gravity": 80,
                    "numIter": 1000,
                    "initialTemp": 200,
                    "coolingFactor": 0.95,
                    "minTemp": 1.0
                },
                message="Graph visualization generated successfully"
            ).dict()
        )
        
    except (ServiceUnavailable, Neo4jDatabaseError) as e:
        logger.error(f"Database error: {str(e)}")
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
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "detail": {
                    "error_type": ErrorType.INTERNAL_ERROR.value,
                    "message": "An unexpected error occurred"
                }
            }
        )

@router.options("/visualize-argument-dag")
async def options_visualize_argument_dag(request: Request, response: Response):
    """Handle CORS preflight requests"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key"
    return JSONResponse(status_code=200, content={"message": "OK"})
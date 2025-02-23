# rational_onion/api/argument_verification.py

from fastapi import APIRouter, Depends, HTTPException, Request
from neo4j import AsyncSession
from neo4j.exceptions import ServiceUnavailable, DatabaseError as Neo4jDatabaseError
from rational_onion.api.dependencies import limiter, get_db
from rational_onion.models.toulmin_model import ArgumentRequest
from rational_onion.api.errors import (
    GraphError, DatabaseError, ValidationError, ErrorType, 
    BaseAPIError, BaseError
)
from rational_onion.config import get_settings
from typing import Dict, Any, Optional, List
from neo4j.graph import Node, Relationship, Path

router = APIRouter()
settings = get_settings()

@router.get("/verify-argument-structure", response_model=Dict[str, Any])
@router.post("/verify-argument-structure", response_model=Dict[str, Any])
@limiter.limit("10/minute")
async def verify_argument_structure(
    request: Request,
    argument: Optional[ArgumentRequest] = None,
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Verify the logical structure and consistency of stored arguments"""
    try:
        # For GET requests without specific argument, verify entire graph
        if argument is None:
            # Check for cycles in entire graph
            query = """
            MATCH path = (start)-[:SUPPORTS|JUSTIFIES*]->(end)
            WHERE id(start) = id(end)
            RETURN path
            """
            try:
                result = await session.run(query)
                records = await result.data()
            except (ServiceUnavailable, Neo4jDatabaseError) as e:
                raise DatabaseError(str(e))
            
            if records:
                raise GraphError("Cycle detected in argument graph")

            # Check for orphaned nodes
            query = """
            MATCH (n:Argument)
            WHERE NOT (n)-[:SUPPORTS|JUSTIFIES]-() 
            AND NOT ()-[:SUPPORTS|JUSTIFIES]->(n)
            RETURN n
            """
            result = await session.run(query)
            records = await result.data()
            if records:
                raise ValidationError(field="graph_structure", message="Orphaned nodes found in argument graph")

            return {
                "status": "success",
                "has_cycles": False,
                "message": "Graph structure verified successfully",
                "orphaned_nodes": []  # Added to match test expectations
            }

        # For POST requests with specific argument
        if argument.argument_id is None:
            raise ValidationError(field="argument_id", message="Argument ID is required for verification")

        try:
            query = """
            MATCH path = (start)-[:SUPPORTS|JUSTIFIES*]->(end)
            WHERE id(start) = $argument_id
            AND id(end) = $argument_id
            RETURN path
            """
            result = await session.run(query, {"argument_id": argument.argument_id})
            records = await result.data()
            if records:
                raise GraphError("Cycle detected in argument graph")

            # Check for orphaned nodes
            query = """
            MATCH (n:Argument)
            WHERE NOT (n)-[:SUPPORTS|JUSTIFIES]-() 
            AND NOT ()-[:SUPPORTS|JUSTIFIES]->(n)
            RETURN n
            """
            result = await session.run(query)
            records = await result.data()
            if records:
                raise ValidationError(field="graph_structure", message="Orphaned nodes found in argument graph")

            # Verify relationship validity
            query = """
            MATCH (n:Argument)-[r]->(m)
            WHERE type(r) NOT IN ['SUPPORTS', 'JUSTIFIES']
            RETURN r
            """
            result = await session.run(query)
            records = await result.data()
            if records:
                raise ValidationError(field="relationship_type", message="Invalid relationship types found")

        except (ServiceUnavailable, Neo4jDatabaseError) as e:
            raise DatabaseError(str(e))

        return {
            "status": "success",
            "message": "Argument structure verified successfully",
            "has_cycles": False,
            "orphaned_nodes": []  # Added to match test expectations
        }

    except GraphError as e:
        raise BaseAPIError(
            error_type=ErrorType.GRAPH_ERROR,
            message=str(e),
            status_code=400,
            details={"error": str(e)}
        )
    except ValidationError as e:
        raise BaseAPIError(
            error_type=ErrorType.VALIDATION_ERROR,
            message=str(e),
            status_code=400,  # Changed from 422 to match test expectations
            details={"field": e.field}
        )
    except DatabaseError as e:
        raise BaseAPIError(
            error_type=ErrorType.DATABASE_ERROR,
            message=str(e),
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
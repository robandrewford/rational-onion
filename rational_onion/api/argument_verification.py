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
from pydantic import BaseModel

router = APIRouter()
settings = get_settings()

class VerificationRequest(BaseModel):
    argument_id: Optional[str] = None

class VerificationResponse(BaseModel):
    status: str
    message: str
    is_valid: bool
    has_cycles: bool
    orphaned_nodes: List[str]

@router.get("/verify-argument-structure", response_model=VerificationResponse)
@router.post("/verify-argument-structure", response_model=VerificationResponse)
@limiter.limit("10/minute")
async def verify_argument_structure(
    request: Request,
    argument: Optional[VerificationRequest] = None,
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Verify the logical structure and consistency of stored arguments"""
    try:
        # For POST requests, argument is required
        if request.method == "POST" and argument is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_type": ErrorType.VALIDATION_ERROR.value,
                    "message": "Request body is required",
                    "details": {"field": "argument"}
                }
            )
        
        # For POST requests with empty/missing argument_id
        if request.method == "POST" and (not argument or not argument.argument_id):
            raise HTTPException(
                status_code=422,
                detail={
                    "error_type": ErrorType.VALIDATION_ERROR.value,
                    "message": "Argument ID is required",
                    "details": {"field": "argument_id"}
                }
            )
        
        # For GET requests or when no argument_id provided
        if argument is None or argument.argument_id is None:
            try:
                # Check for cycles in entire graph
                query = """
                MATCH path = (start:Claim)-[:SUPPORTS|JUSTIFIES*]->(end:Claim)
                WHERE elementId(start) = elementId(end)
                RETURN path
                """
                result = await session.run(query)
                records = await result.data()
                
                if records:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error_type": ErrorType.VALIDATION_ERROR.value,
                            "message": "Cycle detected in argument graph",
                            "details": {"field": "graph_structure"}
                        }
                    )
                
                # Check for invalid relationships first
                query = """
                MATCH (n:Claim)-[r]->(m)
                WHERE NOT type(r) IN ['SUPPORTS', 'JUSTIFIES']
                WITH type(r) as invalid_type
                RETURN collect(invalid_type) as invalid_types
                """
                result = await session.run(query)
                records = await result.data()
                if records and records[0].get('invalid_types'):
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error_type": ErrorType.VALIDATION_ERROR.value,
                            "message": "Invalid relationship types found",
                            "details": {"field": "relationship_type"}
                        }
                    )
                
                # Check for orphaned nodes
                query = """
                MATCH (n:Claim)
                WHERE NOT EXISTS((n)-[:SUPPORTS|JUSTIFIES]-())
                AND NOT EXISTS(()-[:SUPPORTS|JUSTIFIES]->(n))
                RETURN n
                """
                result = await session.run(query)
                records = await result.data()
                
                if records:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error_type": ErrorType.VALIDATION_ERROR.value,
                            "message": "Orphaned nodes found in argument graph",
                            "details": {"field": "graph_structure"}
                        }
                    )
                
                return {
                    "status": "success",
                    "message": "Graph structure verified successfully",
                    "is_valid": True,
                    "has_cycles": False,
                    "orphaned_nodes": []
                }
            except (ServiceUnavailable, Neo4jDatabaseError) as e:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error_type": ErrorType.DATABASE_ERROR.value,
                        "message": str(e),
                        "details": {"error": str(e)}
                    }
                )

        # For POST requests with specific argument
        else:
            if argument.argument_id is None:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error_type": ErrorType.VALIDATION_ERROR.value,
                        "message": "Argument ID is required for verification",
                        "details": {"field": "argument_id"}
                    }
                )

            # Verify the argument exists first
            try:
                query = """
                MATCH (n:Claim)
                WHERE elementId(n) = $argument_id
                RETURN n
                """
                result = await session.run(query, {"argument_id": argument.argument_id})
                records = await result.data()
                if not records:
                    raise HTTPException(
                        status_code=404,
                        detail={
                            "error_type": ErrorType.VALIDATION_ERROR.value,
                            "message": "Argument not found",
                            "details": {"field": "argument_id"}
                        }
                    )
            except (ServiceUnavailable, Neo4jDatabaseError) as e:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error_type": ErrorType.DATABASE_ERROR.value,
                        "message": str(e),
                        "details": {"error": str(e)}
                    }
                )

            # Check for cycles
            try:
                query = """
                MATCH path = (start:Claim)-[:SUPPORTS|JUSTIFIES*]->(end:Claim)
                WHERE elementId(start) = $argument_id
                AND elementId(end) = $argument_id
                RETURN path
                """
                result = await session.run(query, {"argument_id": argument.argument_id})
                records = await result.data()
                if records:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error_type": ErrorType.VALIDATION_ERROR.value,
                            "message": "Cycle detected in argument graph",
                            "details": {"field": "graph_structure"}
                        }
                    )
            except (ServiceUnavailable, Neo4jDatabaseError) as e:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error_type": ErrorType.DATABASE_ERROR.value,
                        "message": str(e),
                        "details": {"error": str(e)}
                    }
                )

            # Verify relationship validity first
            try:
                query = """
                MATCH (n:Claim)-[r]->(m)
                WHERE elementId(n) = $argument_id
                AND NOT type(r) IN ['SUPPORTS', 'JUSTIFIES']
                WITH type(r) as invalid_type
                RETURN collect(invalid_type) as invalid_types
                """
                result = await session.run(query, {"argument_id": argument.argument_id})
                records = await result.data()
                if records and records[0].get('invalid_types'):
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error_type": ErrorType.VALIDATION_ERROR.value,
                            "message": "Invalid relationship types found",
                            "details": {"field": "relationship_type"}
                        }
                    )
            except (ServiceUnavailable, Neo4jDatabaseError) as e:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error_type": ErrorType.DATABASE_ERROR.value,
                        "message": str(e),
                        "details": {"error": str(e)}
                    }
                )

            # Check for orphaned nodes last
            try:
                query = """
                MATCH (n:Claim)
                WHERE elementId(n) = $argument_id
                AND NOT EXISTS((n)-[:SUPPORTS|JUSTIFIES]-())
                AND NOT EXISTS(()-[:SUPPORTS|JUSTIFIES]->(n))
                RETURN n
                """
                result = await session.run(query, {"argument_id": argument.argument_id})
                records = await result.data()
                if records:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error_type": ErrorType.VALIDATION_ERROR.value,
                            "message": "Orphaned nodes found in argument graph",
                            "details": {"field": "graph_structure"}
                        }
                    )
            except (ServiceUnavailable, Neo4jDatabaseError) as e:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error_type": ErrorType.DATABASE_ERROR.value,
                        "message": str(e),
                        "details": {"error": str(e)}
                    }
                )

            return {
                "status": "success",
                "message": "Argument structure verified successfully",
                "is_valid": True,
                "has_cycles": False,
                "orphaned_nodes": []
            }

    except ValidationError as e:
        if "argument_id" in str(e):  # Argument not found or invalid ID
            raise HTTPException(
                status_code=422,
                detail={
                    "error_type": ErrorType.VALIDATION_ERROR.value,
                    "message": str(e),
                    "details": {"field": e.field}
                }
            )
        else:  # Other validation errors (cycles, orphans, etc)
            raise HTTPException(
                status_code=400,
                detail={
                    "error_type": ErrorType.VALIDATION_ERROR.value,
                    "message": str(e),
                    "details": {"field": e.field}
                }
            )
    except GraphError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error_type": ErrorType.GRAPH_ERROR.value,
                "message": str(e),
                "details": {"error": str(e)}
            }
        )
    except (ServiceUnavailable, Neo4jDatabaseError) as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": ErrorType.DATABASE_ERROR.value,
                "message": str(e),
                "details": {"error": str(e)}
            }
        )
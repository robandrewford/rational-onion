# rational_onion/api/argument_verification.py

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from neo4j import AsyncSession
from neo4j.exceptions import ServiceUnavailable, DatabaseError as Neo4jDatabaseError
from rational_onion.api.dependencies import limiter, get_db, verify_api_key
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

@router.get("/verify-argument-structure")
@router.post("/verify-argument-structure")
@limiter.limit("100/minute")
async def verify_argument_structure(
    request: Request,
    argument: Optional[VerificationRequest] = None,
    session: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
) -> JSONResponse:
    """Verify the logical structure and consistency of stored arguments"""
    try:
        # For POST requests, argument is required
        if request.method == "POST" and argument is None:
            return JSONResponse(
                status_code=422,
                content={
                    "detail": {
                        "error_type": ErrorType.VALIDATION_ERROR.value,
                        "message": "Request body is required"
                    }
                }
            )
        
        # For POST requests with empty/missing argument_id
        if request.method == "POST" and (not argument or not argument.argument_id):
            return JSONResponse(
                status_code=422,
                content={
                    "detail": {
                        "error_type": ErrorType.VALIDATION_ERROR.value,
                        "message": "Argument ID is required"
                    }
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
                    return JSONResponse(
                        status_code=400,
                        content={
                            "detail": {
                                "error_type": ErrorType.VALIDATION_ERROR.value,
                                "message": "Cycle detected in argument graph"
                            }
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
                    return JSONResponse(
                        status_code=400,
                        content={
                            "detail": {
                                "error_type": ErrorType.VALIDATION_ERROR.value,
                                "message": "Invalid relationship types found"
                            }
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
                    return JSONResponse(
                        status_code=400,
                        content={
                            "detail": {
                                "error_type": ErrorType.VALIDATION_ERROR.value,
                                "message": "Orphaned nodes found in argument graph"
                            }
                        }
                    )
                
                return JSONResponse(
                    status_code=200,
                    content=VerificationResponse(
                        status="success",
                        message="Graph structure verified successfully",
                        is_valid=True,
                        has_cycles=False,
                        orphaned_nodes=[]
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

        # For POST requests with specific argument
        else:
            if argument.argument_id is None:
                return JSONResponse(
                    status_code=422,
                    content={
                        "detail": {
                            "error_type": ErrorType.VALIDATION_ERROR.value,
                            "message": "Argument ID is required for verification"
                        }
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
                    return JSONResponse(
                        status_code=200,
                        content=VerificationResponse(
                            status="success",
                            message="Argument not found",
                            is_valid=False,
                            has_cycles=False,
                            orphaned_nodes=[]
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
                    return JSONResponse(
                        status_code=400,
                        content={
                            "detail": {
                                "error_type": ErrorType.VALIDATION_ERROR.value,
                                "message": "Cycle detected in argument graph"
                            }
                        }
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
                    return JSONResponse(
                        status_code=400,
                        content={
                            "detail": {
                                "error_type": ErrorType.VALIDATION_ERROR.value,
                                "message": "Invalid relationship types found"
                            }
                        }
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
                    return JSONResponse(
                        status_code=400,
                        content={
                            "detail": {
                                "error_type": ErrorType.VALIDATION_ERROR.value,
                                "message": "Orphaned nodes found in argument graph"
                            }
                        }
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

            # If all checks pass, return success
            return JSONResponse(
                status_code=200,
                content=VerificationResponse(
                    status="success",
                    message="Argument structure verified successfully",
                    is_valid=True,
                    has_cycles=False,
                    orphaned_nodes=[]
                ).dict()
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "detail": {
                    "error_type": ErrorType.UNKNOWN_ERROR.value,
                    "message": "An unexpected error occurred"
                }
            }
        )
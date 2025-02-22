# rational_onion/api/argument_verification.py

from fastapi import APIRouter, Depends, HTTPException, Request
from neo4j import AsyncSession
from rational_onion.api.dependencies import limiter
from rational_onion.models.toulmin_model import ArgumentRequest
from rational_onion.api.errors import GraphError, DatabaseError, ValidationError
from rational_onion.config import get_settings
from typing import Dict, Any

router = APIRouter()
settings = get_settings()

@router.post("/verify-argument-structure", response_model=Dict[str, Any])
@limiter.limit("10/minute")
async def verify_argument_structure(
    request: Request,
    argument: ArgumentRequest,
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Verify the logical structure and consistency of stored arguments"""
    try:
        # Check for cycles in argument graph
        query = """
        MATCH path = (start)-[:SUPPORTS|JUSTIFIES*]->(end)
        WHERE id(start) = $argument_id
        AND id(end) = $argument_id
        RETURN path
        """
        result = await session.run(query, {"argument_id": argument.id})
        records = await result.fetch_all()
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
        records = await result.fetch_all()
        if records:
            raise ValidationError("Orphaned nodes found in argument graph")

        # Verify relationship validity
        query = """
        MATCH (n:Argument)-[r]->(m:Argument)
        WHERE type(r) NOT IN ['SUPPORTS', 'JUSTIFIES']
        RETURN r
        """
        result = await session.run(query)
        records = await result.fetch_all()
        if records:
            raise ValidationError("Invalid relationship types found")

        return {
            "status": "success",
            "message": "Argument structure verified successfully"
        }

    except GraphError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error_type": "GRAPH_ERROR",
                "message": str(e)
            }
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error_type": "VALIDATION_ERROR",
                "message": str(e)
            }
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": "DATABASE_ERROR",
                "message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        )
# rational_onion/api/argument_processing.py

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from rational_onion.services.neo4j_service import driver
from rational_onion.models.toulmin_model import ArgumentRequest, ArgumentResponse
from rational_onion.config import get_settings
from rational_onion.api.errors import (
    ValidationError, ArgumentError, DatabaseError, 
    ErrorType, BaseAPIError
)
from rational_onion.api.dependencies import limiter, get_db
from neo4j import AsyncSession
from neo4j.exceptions import ServiceUnavailable, DatabaseError as Neo4jDatabaseError

router = APIRouter()

settings = get_settings()

def validate_argument_length(argument: ArgumentRequest) -> None:
    """Validate argument field lengths"""
    if len(argument.claim) > settings.MAX_CLAIM_LENGTH:
        raise ValidationError(
            f"Claim exceeds maximum length of {settings.MAX_CLAIM_LENGTH} characters",
            field="claim"
        )
    if len(argument.grounds) > settings.MAX_GROUNDS_LENGTH:
        raise ValidationError(
            f"Grounds exceed maximum length of {settings.MAX_GROUNDS_LENGTH} characters",
            field="grounds"
        )
    if len(argument.warrant) > settings.MAX_WARRANT_LENGTH:
        raise ValidationError(
            f"Warrant exceeds maximum length of {settings.MAX_WARRANT_LENGTH} characters",
            field="warrant"
        )

@router.post("/insert-argument", response_model=Dict[str, Any])
@limiter.limit("10/minute")
async def insert_argument(
    request: Request,
    argument: ArgumentRequest,
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Insert a new argument into the system using Toulmin's model"""
    try:
        # Validate argument lengths
        validate_argument_length(argument)

        # Insert argument into Neo4j
        query = """
        CREATE (a:Argument {
            claim: $claim,
            grounds: $grounds,
            warrant: $warrant,
            created_at: datetime()
        })
        RETURN id(a) as argument_id
        """
        try:
            result = await session.run(
                query,
                {
                    "claim": argument.claim,
                    "grounds": argument.grounds,
                    "warrant": argument.warrant
                }
            )
            record = await result.single()
            
            if not record:
                raise DatabaseError("Failed to create argument")

            return {
                "status": "success",
                "message": "Argument inserted successfully",
                "argument_id": record["argument_id"]
            }

        except (ServiceUnavailable, Neo4jDatabaseError) as e:
            raise DatabaseError(str(e))

    except ValidationError as e:
        raise BaseAPIError(
            error_type=ErrorType.VALIDATION_ERROR,
            message=str(e),
            status_code=422,
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
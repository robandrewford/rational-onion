# rational_onion/api/argument_processing.py

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from rational_onion.services.neo4j_service import driver
from rational_onion.models.toulmin_model import ArgumentRequest, ArgumentResponse, InsertArgumentResponse
from pydantic import BaseModel
from rational_onion.config import get_settings
from rational_onion.api.errors import (
    ValidationError, ArgumentError, DatabaseError, 
    ErrorType, BaseAPIError
)
from rational_onion.api.dependencies import limiter, get_db, verify_api_key
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

# Add RelationshipRequest model
class RelationshipRequest(BaseModel):
    source_id: str
    target_id: str
    relationship_type: str

# Add CreateRelationshipResponse model
class CreateRelationshipResponse(BaseModel):
    message: str
    relationship_id: str

@router.post("/insert-argument", response_model=InsertArgumentResponse)
@limiter.limit("100/minute")
async def insert_argument(
    request: Request,
    response: Response,
    argument: ArgumentRequest,
    api_key: str = Depends(verify_api_key),
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Insert a new argument into the database"""
    try:
        # Validate argument field lengths
        validate_argument_length(argument)
        
        query = """
            CREATE (a:Argument {
                claim: $claim,
                grounds: $grounds,
                warrant: $warrant,
                created_at: datetime()
            })
            RETURN elementId(a) as argument_id
        """
        
        params = {
            "claim": argument.claim,
            "grounds": argument.grounds,
            "warrant": argument.warrant
        }
        
        if argument.rebuttal:
            query = """
                CREATE (a:Argument {
                    claim: $claim,
                    grounds: $grounds,
                    warrant: $warrant,
                    rebuttal: $rebuttal,
                    created_at: datetime()
                })
                RETURN elementId(a) as argument_id
            """
            params["rebuttal"] = argument.rebuttal
            
        result = await session.run(query, params)
        record = await result.single()
        if not record:
            raise BaseAPIError(
                error_type=ErrorType.DATABASE_ERROR,
                message="Failed to create argument",
                status_code=500,
                details={"error": "No record returned"}
            )
        
        # Create response data
        response_data = {
            "argument_id": str(record["argument_id"]),
            "message": "Argument created successfully"
        }
        
        # Return the response directly without creating a JSONResponse
        # This allows FastAPI to handle the response and add the rate limit headers
        return response_data
    
    except (ServiceUnavailable, Neo4jDatabaseError) as e:
        raise BaseAPIError(
            error_type=ErrorType.DATABASE_ERROR,
            message="Database operation failed",
            status_code=500,
            details={"error": str(e)}
        )
    except ValidationError as e:
        raise BaseAPIError(
            error_type=ErrorType.VALIDATION_ERROR,
            message=str(e),
            status_code=422,
            details={"field": e.field}
        )
    except Exception as e:
        raise BaseAPIError(
            error_type=ErrorType.INTERNAL_ERROR,
            message="An unexpected error occurred",
            status_code=500,
            details={"error": str(e)}
        )

@router.post("/create-relationship", response_model=CreateRelationshipResponse)
@limiter.limit("100/minute")
async def create_relationship(
    request: Request,
    response: Response,
    relationship: RelationshipRequest,
    api_key: str = Depends(verify_api_key),
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Create a relationship between two arguments"""
    try:
        # Validate relationship type
        valid_relationship_types = ["SUPPORTS", "CHALLENGES", "JUSTIFIES"]
        if relationship.relationship_type not in valid_relationship_types:
            raise ValidationError(
                f"Invalid relationship type. Must be one of: {', '.join(valid_relationship_types)}",
                field="relationship_type"
            )
        
        # Check if both arguments exist
        query = """
            MATCH (a1:Argument)
            WHERE elementId(a1) = $source_id
            MATCH (a2:Argument)
            WHERE elementId(a2) = $target_id
            RETURN a1, a2
        """
        
        result = await session.run(query, {
            "source_id": relationship.source_id,
            "target_id": relationship.target_id
        })
        
        record = await result.single()
        if not record:
            raise ValidationError(
                "One or both arguments not found",
                field="source_id/target_id"
            )
        
        # Create relationship
        query = f"""
            MATCH (a1:Argument)
            WHERE elementId(a1) = $source_id
            MATCH (a2:Argument)
            WHERE elementId(a2) = $target_id
            CREATE (a1)-[r:{relationship.relationship_type}]->(a2)
            RETURN elementId(r) as relationship_id
        """
        
        result = await session.run(query, {
            "source_id": relationship.source_id,
            "target_id": relationship.target_id
        })
        
        record = await result.single()
        if not record:
            raise BaseAPIError(
                error_type=ErrorType.DATABASE_ERROR,
                message="Failed to create relationship",
                status_code=500,
                details={"error": "No record returned"}
            )
        
        # Create response data
        response_data = {
            "message": "Relationship created successfully",
            "relationship_id": str(record["relationship_id"])
        }
        
        return response_data
    
    except (ServiceUnavailable, Neo4jDatabaseError) as e:
        raise BaseAPIError(
            error_type=ErrorType.DATABASE_ERROR,
            message="Database operation failed",
            status_code=500,
            details={"error": str(e)}
        )
    except ValidationError as e:
        raise BaseAPIError(
            error_type=ErrorType.VALIDATION_ERROR,
            message=str(e),
            status_code=422,
            details={"field": e.field}
        )
    except Exception as e:
        raise BaseAPIError(
            error_type=ErrorType.INTERNAL_ERROR,
            message="An unexpected error occurred",
            status_code=500,
            details={"error": str(e)}
        )
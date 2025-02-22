# rational_onion/api/argument_processing.py

from fastapi import APIRouter, Depends, HTTPException
from rational_onion.services.neo4j_service import driver
from rational_onion.models.toulmin_model import ArgumentRequest, ArgumentResponse
from rational_onion.config import get_settings

router = APIRouter()

settings = get_settings()

@router.post("/insert-argument", response_model=ArgumentResponse)
async def insert_argument(arg: ArgumentRequest):
    """
    Insert a new argument into the system using Toulmin's model.
    
    Parameters:
        arg: ArgumentRequest object containing:
            - claim: Main position being argued
            - grounds: Evidence supporting the claim
            - warrant: Reasoning connecting grounds to claim
            - rebuttal (optional): Potential counter-arguments
        
    Returns:
        ArgumentResponse containing:
            - Processed argument components
            - Confirmation message
            - Argument ID for future reference
        
    Raises:
        ArgumentError: If argument structure violates Toulmin model rules
        ValidationError: If component lengths exceed limits
        DatabaseError: If Neo4j storage operation fails
    """
    try:
        async with driver.session() as session:
            await session.run(
                """
                MERGE (c:Claim {text: $claim})
                MERGE (g:Grounds {text: $grounds})
                MERGE (w:Warrant {text: $warrant})
                MERGE (g)-[:SUPPORTED_BY]->(c)
                MERGE (w)-[:JUSTIFIED_BY]->(c)
                FOREACH(_ IN CASE WHEN $rebuttal IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (r:Rebuttal {text: $rebuttal})
                    MERGE (r)-[:CHALLENGES]->(c)
                )
                """,
                claim=arg.claim,
                grounds=arg.grounds,
                warrant=arg.warrant,
                rebuttal=arg.rebuttal
            )
        return {
            "claim": arg.claim,
            "grounds": arg.grounds,
            "warrant": arg.warrant,
            "rebuttal": arg.rebuttal,
            "message": "Argument successfully inserted."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Argument insertion failed: {e}")

def validate_argument_length(argument: Dict[str, str]) -> None:
    """Validate argument component lengths"""
    if len(argument["claim"]) > settings.MAX_CLAIM_LENGTH:
        raise ValidationError("Claim exceeds maximum length")
    if len(argument["grounds"]) > settings.MAX_GROUNDS_LENGTH:
        raise ValidationError("Grounds exceed maximum length")
    if len(argument["warrant"]) > settings.MAX_WARRANT_LENGTH:
        raise ValidationError("Warrant exceeds maximum length")
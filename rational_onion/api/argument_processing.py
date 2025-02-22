# rational_onion/api/argument_processing.py

from fastapi import APIRouter, Depends, HTTPException
from rational_onion.services.neo4j_service import driver
from rational_onion.models.toulmin_model import ArgumentRequest, ArgumentResponse

router = APIRouter()

@router.post("/insert-argument", response_model=ArgumentResponse)
async def insert_argument(arg: ArgumentRequest):
    """
    Inserts a Toulmin-structured argument into Neo4j.
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
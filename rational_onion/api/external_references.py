# rational_onion/api/external_references.py

from fastapi import APIRouter, HTTPException
from typing import List, Tuple
from rational_onion.services.neo4j_service import driver
from rational_onion.services.nlp_service import rank_references_with_embeddings

router = APIRouter()

@router.get("/fetch-external-references", response_model=List[Tuple[str, float, int, str]])
async def fetch_external_references_api(query: str):
    """
    Retrieves and ranks scholarly references from multiple sources using 
    embedding-based expanded queries, prioritizing citation count & publication year.
    """
    try:
        references = await rank_references_with_embeddings(query)
        return references
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch external references: {e}")
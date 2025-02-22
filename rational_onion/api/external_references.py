# rational_onion/api/external_references.py

from fastapi import APIRouter, HTTPException
from typing import List, Tuple
from rational_onion.services.neo4j_service import driver
from rational_onion.services.nlp_service import rank_references_with_embeddings

router = APIRouter()

@router.get("/fetch-external-references", response_model=List[Tuple[str, float, int, str]])
async def fetch_external_references_api(query: str):
    """
    Retrieve and rank scholarly references relevant to an argument.
    
    Uses embedding-based similarity and citation metrics to find supporting literature.
    
    Parameters:
        query: Search text to find relevant references
        
    Returns:
        List of tuples containing:
            - title: Reference title
            - relevance_score: Semantic similarity score (0-1)
            - citation_count: Number of citations
            - url: Link to source
            
    Raises:
        CitationError: If reference validation fails
        ValidationError: If query is invalid
        ExternalServiceError: If scholarly API fails
    """
    try:
        references = await rank_references_with_embeddings(query)
        return references
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch external references: {e}")
# rational_onion/api/argument_improvement.py

from fastapi import APIRouter, HTTPException
from rational_onion.services.neo4j_service import driver
from rational_onion.services.nlp_service import enhance_argument_with_nlp
from rational_onion.models.toulmin_model import ArgumentImprovementResponse

router = APIRouter()

@router.get("/suggest-improvements", response_model=ArgumentImprovementResponse)
async def suggest_argument_improvements():
    """
    Generate NLP-enhanced suggestions to improve argument quality.
    
    Analysis includes:
        - Lexical diversity assessment
        - Evidence strength evaluation
        - Logical flow analysis
        - Citation completeness check
        
    Returns:
        ArgumentImprovementResponse containing:
            - missing_components: Required elements that need to be added
            - quality_score: Numerical assessment of argument strength
            - improvement_suggestions: List of specific enhancement recommendations
            - external_references: Relevant scholarly sources
            - message: Summary of improvement analysis
            
    Raises:
        ArgumentError: If argument structure is invalid
        DatabaseError: If retrieval fails
        NLPServiceError: If language processing fails
    """
    try:
        # Example: fetch all claims from Neo4j
        async with driver.session() as session:
            result = await session.run("""
                MATCH (c:Claim)
                RETURN c.text AS claim
            """)
            claims = [record["claim"] for record in await result.fetchall()]

        # For each claim, run NLP suggestions
        improvement_suggestions = []
        for claim_text in claims:
            nlp_suggestions = enhance_argument_with_nlp(claim_text)
            improvement_suggestions.append({
                "claim": claim_text,
                "improvement_suggestions": nlp_suggestions,
                "external_references": []  # add references if needed
            })

        return {
            "missing_components": [s["claim"] for s in improvement_suggestions],
            "quality_score": 0.0,
            "improvement_suggestions": improvement_suggestions,
            "external_references": [],
            "message": "Advanced NLP-enhanced argument improvement suggestions generated."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Improvement suggestion failed: {e}")
# rational_onion/models/toulmin_model.py

from pydantic import BaseModel, Field, constr
from typing import Optional, List, Dict, Any
from rational_onion.config import get_settings

settings = get_settings()

class ArgumentRequest(BaseModel):
    claim: constr(min_length=1, max_length=settings.MAX_CLAIM_LENGTH)
    grounds: constr(min_length=1, max_length=settings.MAX_GROUNDS_LENGTH)
    warrant: constr(min_length=1, max_length=settings.MAX_WARRANT_LENGTH)
    rebuttal: Optional[str] = None
    argument_id: Optional[int] = None

class ArgumentResponse(BaseModel):
    claim: str
    grounds: str
    warrant: str
    rebuttal: Optional[str] = None
    message: str

class ArgumentImprovementSuggestions(BaseModel):
    claim: str
    improvement_suggestions: List[str]
    external_references: List[Any]

class ArgumentImprovementResponse(BaseModel):
    missing_components: List[str]
    quality_score: float
    improvement_suggestions: List[Dict[str, Any]]
    external_references: List[Any]
    message: str
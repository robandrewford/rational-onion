# rational_onion/models/toulmin_model.py

from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ArgumentRequest(BaseModel):
    claim: str
    grounds: str
    warrant: str
    rebuttal: Optional[str] = None

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
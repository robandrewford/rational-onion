# rational_onion/models/dag_models.py

from pydantic import BaseModel
from typing import List, Dict, Any

class DAGResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
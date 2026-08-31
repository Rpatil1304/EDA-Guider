"""
Decision schemas
"""
from pydantic import BaseModel
from typing import List, Any

class DecisionRecord(BaseModel):
    """Record of a decision made by the agent"""
    column: str
    action: str
    parameters: dict
    reasoning: str

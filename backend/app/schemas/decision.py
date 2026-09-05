"""
Decision schemas
"""
from pydantic import BaseModel , Field
from typing import List, Any

class DecisionRecord(BaseModel):
    """Record of a decision made by the agent"""
    column: str
    action: str
    parameters: dict = Field(default_factory=dict)
    reasoning: str

# Now we add information that tells us who/what produced the decision and how confident the system is.

    source : str 
    confidence : float 

    evidence: dict = Field(default_factory=dict)
    status: str 

    evidence_verified: bool = False
    audit_id: str | None = None

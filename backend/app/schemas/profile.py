"""
Data profiling schemas
"""
from pydantic import BaseModel
from typing import Optional, List

class ColumnProfile(BaseModel):
    """Column profile information"""
    name: str
    data_type: str
    null_count: int
    unique_count: int
    duplicates: int

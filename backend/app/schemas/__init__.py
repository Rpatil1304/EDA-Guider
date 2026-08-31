"""
Data schema definitions for request/response validation
"""
from pydantic import BaseModel
from typing import List, Optional, Any

class ProfileSchema(BaseModel):
    """Data profile schema"""
    column_name: str
    data_type: str
    missing_count: int
    null_percentage: float
    unique_count: int

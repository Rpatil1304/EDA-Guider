"""
Report schemas
"""
from pydantic import BaseModel
from typing import List, Dict

class AnalysisReport(BaseModel):
    """Complete analysis report"""
    dataset_name: str
    total_rows: int
    total_columns: int
    insights: List[str]
    visualizations: List[str]

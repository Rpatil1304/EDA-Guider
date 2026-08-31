"""
Chart builder
"""
import pandas as pd

class ChartBuilder:
    """Build chart specifications"""
    
    def build_scatter(self, df: pd.DataFrame, x: str, y: str) -> dict:
        """Build scatter plot specification"""
        return {
            'type': 'scatter',
            'x': x,
            'y': y
        }

"""
Statistical analysis
"""
import pandas as pd

class StatisticsAnalyzer:
    """Compute statistical summaries"""
    
    @staticmethod
    def compute_stats(df: pd.DataFrame) -> dict:
        """Compute statistics for numeric columns"""
        return df.describe().to_dict()

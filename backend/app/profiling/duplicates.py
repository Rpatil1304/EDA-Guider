"""
Duplicate detection
"""
import pandas as pd

class DuplicateDetector:
    """Detect duplicate rows and values"""
    
    @staticmethod
    def find_duplicates(df: pd.DataFrame, subset: list = None) -> list:
        """Find duplicate rows"""
        return df.duplicated(subset=subset).sum()

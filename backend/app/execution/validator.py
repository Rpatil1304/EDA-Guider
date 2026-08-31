"""
Data validation
"""
import pandas as pd

class Validator:
    """Validate data transformations"""
    
    @staticmethod
    def validate(df: pd.DataFrame) -> bool:
        """Validate data integrity"""
        return len(df) > 0 and len(df.columns) > 0

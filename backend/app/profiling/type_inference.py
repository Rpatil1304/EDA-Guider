"""
Type inference module
"""
import pandas as pd
from typing import Dict

class TypeInference:
    """Infer data types for columns"""
    
    @staticmethod
    def infer_types(df: pd.DataFrame) -> Dict[str, str]:
        """Infer column data types"""
        return {col: str(df[col].dtype) for col in df.columns}

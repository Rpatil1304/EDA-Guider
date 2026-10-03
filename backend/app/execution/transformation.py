"""
Data transformations
"""
import pandas as pd
import numpy as np

class Transformer:
    """Apply data transformations"""
    
    @staticmethod
    def log_transform(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Apply log transformation"""
        df[column] = df[column].apply(lambda x: np.log(x) if x > 0 else x)
        return df

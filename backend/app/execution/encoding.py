"""
Categorical encoding
"""
import pandas as pd

class Encoder:
    """Handle categorical variable encoding"""
    
    @staticmethod
    def one_hot_encode(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """One-hot encode categorical column"""
        return pd.get_dummies(df, columns=[column])

"""
Imputation strategies
"""
import pandas as pd

class Imputer:
    """Handle missing value imputation"""
    
    @staticmethod
    def impute_mean(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Impute missing values with mean"""
        df[column].fillna(df[column].mean(), inplace=True)
        return df

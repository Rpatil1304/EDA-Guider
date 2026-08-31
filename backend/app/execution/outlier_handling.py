"""
Outlier handling
"""
import pandas as pd

class OutlierHandler:
    """Handle outlier removal or treatment"""
    
    @staticmethod
    def remove_outliers_iqr(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Remove outliers using IQR method"""
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        return df[(df[column] >= Q1 - 1.5*IQR) & (df[column] <= Q3 + 1.5*IQR)]

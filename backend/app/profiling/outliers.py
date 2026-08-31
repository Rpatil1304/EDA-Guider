"""
Outlier detection
"""
import pandas as pd
import numpy as np

class OutlierDetector:
    """Detect outliers in data"""
    
    @staticmethod
    def detect_iqr(df: pd.DataFrame, column: str) -> list:
        """Detect outliers using IQR method"""
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return df[(df[column] < lower_bound) | (df[column] > upper_bound)].index.tolist()

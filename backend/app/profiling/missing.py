"""
Missing data analysis
"""
import pandas as pd

class MissingDataAnalyzer:
    """Analyze missing values in data"""
    
    @staticmethod
    def analyze(df: pd.DataFrame) -> dict:
        """Analyze missing values"""
        return {
            col: {
                'missing_count': df[col].isna().sum(),
                'missing_percentage': (df[col].isna().sum() / len(df)) * 100
            }
            for col in df.columns
        }

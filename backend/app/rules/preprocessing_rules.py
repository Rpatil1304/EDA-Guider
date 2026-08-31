"""
Preprocessing rules
"""

class PreprocessingRules:
    """Define rules for data preprocessing"""
    
    IMPUTATION_STRATEGIES = {
        'mean': 'Use mean for numeric columns',
        'median': 'Use median for numeric columns',
        'forward_fill': 'Forward fill for time series',
        'drop': 'Drop rows with missing values'
    }

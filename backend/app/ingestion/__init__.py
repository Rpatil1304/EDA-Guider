"""
Data ingestion module
"""
import pandas as pd
from pathlib import Path
from typing import Union

class DataLoader:
    """Handles data loading from various file formats"""
    
    @staticmethod
    def load(file_path: Union[str, Path]) -> pd.DataFrame:
        """Load data from file"""
        file_path = Path(file_path)
        
        if file_path.suffix == '.csv':
            return pd.read_csv(file_path)
        elif file_path.suffix in ['.xlsx', '.xls']:
            return pd.read_excel(file_path)
        elif file_path.suffix == '.json':
            return pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

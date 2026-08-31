"""
Main profiler orchestrator
"""
import pandas as pd
from .type_inference import TypeInference
from .missing import MissingDataAnalyzer
from .statistics import StatisticsAnalyzer
from .outliers import OutlierDetector
from .duplicates import DuplicateDetector

class DataProfiler:
    """Orchestrate data profiling"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
    
    def profile(self) -> dict:
        """Generate complete data profile"""
        return {
            'types': TypeInference.infer_types(self.df),
            'missing': MissingDataAnalyzer.analyze(self.df),
            'stats': StatisticsAnalyzer.compute_stats(self.df),
        }

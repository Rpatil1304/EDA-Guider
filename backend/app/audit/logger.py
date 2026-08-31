"""
Audit logger
"""
import logging
from datetime import datetime

class AuditLogger:
    """Log all decisions and transformations"""
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
    
    def log_decision(self, decision: dict):
        """Log a decision"""
        self.logger.info(f"Decision: {decision}")
    
    def log_transformation(self, transformation: dict):
        """Log a data transformation"""
        self.logger.info(f"Transformation: {transformation}")

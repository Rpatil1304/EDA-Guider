"""
Pipeline state management
"""

class PipelineState:
    """Manage pipeline execution state"""
    
    def __init__(self):
        self.current_step = None
        self.data = None
        self.profile = None
        self.decisions = []

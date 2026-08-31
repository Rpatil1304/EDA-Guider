"""
Insight synthesizer
"""

class InsightSynthesizer:
    """Synthesize insights from multiple sources"""
    
    def synthesize(self, statistical_insights: list, agent_insights: list) -> dict:
        """Combine insights from different sources"""
        return {'insights': statistical_insights + agent_insights}

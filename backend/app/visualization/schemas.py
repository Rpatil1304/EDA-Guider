from pydantic import BaseModel, Field


class VisualizationRecommendation(BaseModel):
    rule_id: str
    chart_type: str
    columns: list[str] = Field(default_factory=list)
    reason: str
    confidence: float = 0.0
    priority: str = "medium"


class VisualizationRecommendationProfile(BaseModel):
    recommendations: list[VisualizationRecommendation] = Field(
        default_factory=list
    )
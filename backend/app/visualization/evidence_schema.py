from pydantic import BaseModel, Field


class VisualizationEvidence(BaseModel):
    rule_id: str
    chart_type: str
    columns: list[str] = Field(default_factory=list)

    confidence: float = 0.0
    priority: str = "medium"
    reason: str = ""

    row_count: int = 0

    column_statistics: dict[str, dict] = Field(
        default_factory=dict
    )


class VisualizationEvidenceProfile(BaseModel):
    evidence: list[VisualizationEvidence] = Field(
        default_factory=list
    )
from pydantic import BaseModel, Field


class PreprocessingIssue(BaseModel):
    # "What problem did we find?"

    column: str
    issue: str
    description: str | None = None
    severity: str | None = None


class PreprocessingAction(BaseModel):
    # "What action could address it?"

    columns: list[str]
    action: str
    parameters: dict = Field(
        default_factory=dict
    )
    reason: str


class PreprocessingPlan(BaseModel):

    actions: list[PreprocessingAction] = Field(
        default_factory=list
    )

    reasoning: str
    source: str
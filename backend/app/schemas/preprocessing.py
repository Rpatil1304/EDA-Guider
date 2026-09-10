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
    confidence: float = 0.0
    reason: str


class PreprocessingPlan(BaseModel):

    actions: list[PreprocessingAction] = Field(
        default_factory=list
    )

    reasoning: str
    source: str


class PreprocessingResult(BaseModel):

    # Actions that were actually executed
    executed_actions: list[PreprocessingAction] = Field(
        default_factory=list
    )

    # Actions that were skipped because they
    # require review or are not safe to execute
    skipped_actions: list[PreprocessingAction] = Field(
        default_factory=list
    )

    # Information about changes made during preprocessing
    changes: list[dict] = Field(
        default_factory=list
    )

    # Overall explanation of what happened
    reasoning: str = ""

    # Identifies the component that performed preprocessing
    source: str = "preprocessor"
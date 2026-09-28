from pydantic import BaseModel, Field


class RawDatasetReport(BaseModel):
    row_count: int = 0
    column_count: int = 0

    columns: list[dict] = Field(
        default_factory=list
    )

    total_missing_count: int = 0
    total_missing_percentage: float = 0.0

    warnings: list = Field(
        default_factory=list
    )


class PreprocessingReport(BaseModel):
    summary: dict = Field(
        default_factory=dict
    )

    steps: list[dict] = Field(
        default_factory=list
    )

    changed_columns: list[dict] = Field(
        default_factory=list
    )

    unresolved_columns: list[dict] = Field(
        default_factory=list
    )

    needs_review_columns: list[dict] = Field(
        default_factory=list
    )


class CleanedDatasetReport(BaseModel):
    row_count: int = 0
    column_count: int = 0

    columns: list[dict] = Field(
        default_factory=list
    )

    total_missing_count: int = 0
    total_missing_percentage: float = 0.0


class StatisticalReport(BaseModel):
    numeric_statistics: dict = Field(
        default_factory=dict
    )

    categorical_statistics: dict = Field(
        default_factory=dict
    )

    datetime_statistics: dict = Field(
        default_factory=dict
    )

    boolean_statistics: dict = Field(
        default_factory=dict
    )

    correlation_matrix: dict = Field(
        default_factory=dict
    )


class VisualizationSelection(BaseModel):
    chart_type: str
    columns: list[str] = Field(
        default_factory=list
    )

    reason: str = ""

    confidence: float = 0.0

    priority: str = "medium"


class FinalVisualizationReport(BaseModel):
    selected: list[VisualizationSelection] = Field(
        default_factory=list
    )


class FinalEDAReport(BaseModel):
    raw_dataset: RawDatasetReport = Field(
        default_factory=RawDatasetReport
    )

    preprocessing: PreprocessingReport = Field(
        default_factory=PreprocessingReport
    )

    cleaned_dataset: CleanedDatasetReport = Field(
        default_factory=CleanedDatasetReport
    )

    statistics: StatisticalReport = Field(
        default_factory=StatisticalReport
    )

    visualizations: FinalVisualizationReport = Field(
        default_factory=FinalVisualizationReport
    )
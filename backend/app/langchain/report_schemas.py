"""Pydantic schemas for final EDA report generation."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DatasetReportEvidence(BaseModel):
    """Privacy-safe dataset-level information."""

    row_count: int = 0
    column_count: int = 0

    numeric_columns: list[str] = Field(
        default_factory=list
    )

    categorical_columns: list[str] = Field(
        default_factory=list
    )

    datetime_columns: list[str] = Field(
        default_factory=list
    )

    boolean_columns: list[str] = Field(
        default_factory=list
    )

    missing_value_columns: list[str] = Field(
        default_factory=list
    )


class PreprocessingReportEvidence(BaseModel):
    """Information about preprocessing performed."""

    steps: list[str] = Field(
        default_factory=list
    )

    rows_before: int = 0
    rows_after: int = 0

    columns_before: int = 0
    columns_after: int = 0


class StatisticalReportEvidence(BaseModel):
    """Privacy-safe statistical information."""

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


class VisualizationReportEvidence(BaseModel):
    """Validated visualization information."""

    accepted: list[dict] = Field(
        default_factory=list
    )

    modified: list[dict] = Field(
        default_factory=list
    )

    rejected: list[dict] = Field(
        default_factory=list
    )


class EDAReportEvidence(BaseModel):
    """Complete privacy-safe evidence for final EDA reporting."""

    dataset: DatasetReportEvidence = Field(
        default_factory=DatasetReportEvidence
    )

    preprocessing: PreprocessingReportEvidence = Field(
        default_factory=PreprocessingReportEvidence
    )

    statistics: StatisticalReportEvidence = Field(
        default_factory=StatisticalReportEvidence
    )

    visualizations: VisualizationReportEvidence = Field(
        default_factory=VisualizationReportEvidence
    )
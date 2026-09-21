"""Pydantic schemas for LangChain outputs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SUPPORTED_CHART_TYPES = Literal[
    "histogram",
    "box_plot",
    "bar_chart",
    "pie_chart",
    "scatter_plot",
    "line_chart",
    "grouped_bar_chart",
    "stacked_bar_chart",
    "100_percent_stacked_bar_chart",
    "heatmap",
    "missingness_bar_chart",
    "missingness_heatmap",
    "violin_plot",
    "qq_plot",
    "pair_plot",
]


VALIDATION_DECISIONS = Literal[
    "accepted",
    "modified",
    "rejected",
]


class LLMVisualizationValidation(BaseModel):
    """Validation result for one rule-based visualization."""

    original_chart_type: SUPPORTED_CHART_TYPES = Field(
        description=(
            "The chart type originally recommended by "
            "the deterministic rule engine."
        )
    )

    original_columns: list[str] = Field(
        default_factory=list,
        description=(
            "The columns originally recommended by "
            "the deterministic rule engine."
        )
    )

    decision: VALIDATION_DECISIONS = Field(
        description=(
            "Whether the rule-based recommendation is "
            "accepted, modified, or rejected."
        )
    )

    final_chart_type: SUPPORTED_CHART_TYPES | None = Field(
        default=None,
        description=(
            "The final chart type after validation. "
            "Use null when the recommendation is rejected."
        )
    )

    final_columns: list[str] = Field(
        default_factory=list,
        description=(
            "The final columns to use for the visualization."
        )
    )

    reason: str = Field(
        description=(
            "Explanation for accepting, modifying, or "
            "rejecting the recommendation."
        )
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1."
    )


class LLMVisualizationValidationResponse(BaseModel):
    """Complete visualization validation response."""

    validations: list[LLMVisualizationValidation] = Field(
        default_factory=list,
        description=(
            "Validation results for the rule-based "
            "visualization recommendations."
        )
    )
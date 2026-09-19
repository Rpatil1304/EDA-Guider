"""Build structured evidence for visualization recommendations."""

from __future__ import annotations

from typing import Any

from app.schemas.statistics import StatisticalProfile

from app.visualization.schemas import (
    VisualizationRecommendationProfile,
)

from app.visualization.evidence_schema import (
    VisualizationEvidence,
    VisualizationEvidenceProfile,
)


def _get_column_statistics(
    statistical_profile: StatisticalProfile,
    column: str,
) -> dict[str, Any]:
    """Return statistics for a single column."""

    column_profile = statistical_profile.columns.get(column)

    if column_profile is None:
        return {}

    return column_profile.model_dump()


def _build_recommendation_evidence(
    statistical_profile: StatisticalProfile,
    recommendation: dict[str, Any],
) -> dict[str, Any]:
    """Build privacy-safe evidence for one visualization recommendation."""

    columns = recommendation.get("columns", [])

    evidence: dict[str, Any] = {
        "rule_id": recommendation.get("rule_id"),
        "chart_type": recommendation.get("chart_type"),
        "columns": columns,
        "confidence": recommendation.get("confidence", 0.0),
        "priority": recommendation.get("priority", "medium"),
        "reason": recommendation.get("reason", ""),
        "row_count": statistical_profile.n_rows,
    }

    column_evidence: dict[str, Any] = {}

    for column in columns:
        statistics = _get_column_statistics(
            statistical_profile,
            column,
        )

        if statistics:
            column_evidence[column] = statistics

    evidence["column_statistics"] = column_evidence

    return evidence


def build_visualization_evidence(
    statistical_profile: StatisticalProfile,
    recommendations: VisualizationRecommendationProfile,
) -> VisualizationEvidenceProfile:
    """Build structured evidence for visualization recommendations."""

    profile_data = recommendations.model_dump()

    evidence: list[dict[str, Any]] = []

    for recommendation in profile_data.get(
        "recommendations",
        [],
    ):
        evidence.append(
            _build_recommendation_evidence(
                statistical_profile,
                recommendation,
            )
        )

    return VisualizationEvidenceProfile(
    evidence=[
        VisualizationEvidence(**item)
        for item in evidence
    ]
)
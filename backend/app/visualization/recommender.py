"""Orchestrate visualization recommendation rules."""

from __future__ import annotations

from app.schemas.statistics import StatisticalProfile

from app.visualization.rules import (
    recommend_100_percent_stacked_bar_charts,
    recommend_bar_charts,
    recommend_box_plots,
    recommend_correlation_heatmaps,
    recommend_grouped_bar_charts,
    recommend_histograms,
    recommend_line_charts,
    recommend_missingness_bar_charts,
    recommend_missingness_heatmaps,
    recommend_pair_plots,
    recommend_pie_charts,
    recommend_qq_plots,
    recommend_scatter_plots,
    recommend_stacked_bar_charts,
    recommend_violin_plots,
)

from app.visualization.schemas import (
    VisualizationRecommendation,
    VisualizationRecommendationProfile,
)


def generate_visualization_recommendations(
    statistical_profile: StatisticalProfile,
) -> VisualizationRecommendationProfile:
    """
    Generate visualization recommendations from a statistical profile.

    The function executes all deterministic visualization rules and
    converts their outputs into validated Pydantic models.
    """

    profile_data = statistical_profile.model_dump()

    recommendations: list[VisualizationRecommendation] = []

    rule_functions = [
        recommend_histograms,
        recommend_box_plots,
        recommend_bar_charts,
        recommend_pie_charts,
        recommend_scatter_plots,
        recommend_line_charts,
        recommend_grouped_bar_charts,
        recommend_stacked_bar_charts,
        recommend_100_percent_stacked_bar_charts,
        recommend_correlation_heatmaps,
        recommend_missingness_bar_charts,
        recommend_missingness_heatmaps,
        recommend_violin_plots,
        recommend_qq_plots,
        recommend_pair_plots,
    ]

    for rule_function in rule_functions:

        rule_results = rule_function(
            profile_data
        )

        for result in rule_results:

            recommendations.append(
                VisualizationRecommendation(
                    **result
                )
            )

    return VisualizationRecommendationProfile(
        recommendations=recommendations
    )
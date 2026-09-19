"""Rule definitions for visualization recommendations."""

from __future__ import annotations

from itertools import combinations
from typing import Any


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _get_columns_by_type(
    statistical_profile: dict[str, Any],
    column_type: str,
) -> list[str]:
    """Return column names belonging to a specific semantic type."""

    if column_type == "numeric":
        return list(statistical_profile.get("numeric_columns", {}).keys())

    if column_type == "categorical":
        return list(statistical_profile.get("categorical_columns", {}).keys())

    if column_type == "datetime":
        return list(statistical_profile.get("datetime_columns", {}).keys())

    if column_type == "boolean":
        return list(statistical_profile.get("boolean_columns", {}).keys())

    return []


def _get_unique_count(
    statistical_profile: dict[str, Any],
    column: str,
) -> int:
    """Return unique value count for a column."""

    column_profile = statistical_profile.get(
        "columns",
        {},
    ).get(
        column,
        {},
    )

    unique_count = column_profile.get(
        "unique_count"
    )

    if unique_count is not None:
        return int(unique_count)

    for column_type in (
        "categorical_columns",
        "numeric_columns",
        "datetime_columns",
        "boolean_columns",
    ):
        type_profile = statistical_profile.get(
            column_type,
            {},
        )

        if column in type_profile:
            return int(
                type_profile[column].get(
                    "unique_count",
                    0,
                )
            )

    return 0


def _get_row_count(
    statistical_profile: dict[str, Any],
) -> int:
    """Return dataset row count."""

    return int(
        statistical_profile.get(
            "n_rows",
            statistical_profile.get("row_count", 0),
        )
    )


# ---------------------------------------------------------------------------
# 1. Histogram
# ---------------------------------------------------------------------------

def recommend_histograms(
    statistical_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Recommend histograms for numeric columns."""

    numeric_columns = _get_columns_by_type(
        statistical_profile,
        "numeric",
    )

    recommendations = []

    for column in numeric_columns:
        recommendations.append(
            {
                "rule_id": "NUMERIC_HISTOGRAM",
                "chart_type": "histogram",
                "columns": [column],
                "reason": (
                    f"'{column}' is numeric, so a histogram can show "
                    "its distribution and concentration of values."
                ),
                "confidence": 0.95,
                "priority": "high",
            }
        )

    return recommendations


# ---------------------------------------------------------------------------
# 2. Box Plot
# ---------------------------------------------------------------------------

def recommend_box_plots(
    statistical_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Recommend box plots for numeric columns."""

    numeric_columns = _get_columns_by_type(
        statistical_profile,
        "numeric",
    )

    recommendations = []

    for column in numeric_columns:
        recommendations.append(
            {
                "rule_id": "NUMERIC_BOX_PLOT",
                "chart_type": "box_plot",
                "columns": [column],
                "reason": (
                    f"'{column}' is numeric, so a box plot can show "
                    "its median, quartiles, spread, and potential outliers."
                ),
                "confidence": 0.95,
                "priority": "medium",
            }
        )

    return recommendations


# ---------------------------------------------------------------------------
# 3. Bar Chart
# ---------------------------------------------------------------------------

def recommend_bar_charts(
    statistical_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Recommend bar charts for categorical columns."""

    categorical_columns = _get_columns_by_type(
        statistical_profile,
        "categorical",
    )

    recommendations = []

    for column in categorical_columns:
        recommendations.append(
            {
                "rule_id": "CATEGORICAL_BAR",
                "chart_type": "bar_chart",
                "columns": [column],
                "reason": (
                    f"'{column}' is categorical, so a bar chart can "
                    "show the frequency of its categories."
                ),
                "confidence": 0.95,
                "priority": "high",
            }
        )

    return recommendations


# ---------------------------------------------------------------------------
# 4. Pie / Donut Chart
# ---------------------------------------------------------------------------

def recommend_pie_charts(
    statistical_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Recommend pie/donut charts for low-cardinality categorical columns."""

    categorical_columns = _get_columns_by_type(
        statistical_profile,
        "categorical",
    )

    recommendations = []

    for column in categorical_columns:
        unique_count = _get_unique_count(
            statistical_profile,
            column,
        )

        # Pie/Donut charts become difficult to interpret with many
        # categories, so restrict them to low-cardinality columns.
        if 2 <= unique_count <= 6:
            recommendations.append(
                {
                    "rule_id": "LOW_CARDINALITY_PIE",
                    "chart_type": "pie_donut_chart",
                    "columns": [column],
                    "reason": (
                        f"'{column}' has {unique_count} categories, "
                        "which is a manageable number for showing "
                        "category proportions using a pie or donut chart."
                    ),
                    "confidence": 0.85,
                    "priority": "medium",
                }
            )

    return recommendations


# ---------------------------------------------------------------------------
# 5. Scatter Plot
# ---------------------------------------------------------------------------

def recommend_scatter_plots(
    statistical_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Recommend scatter plots for numeric column pairs."""

    numeric_columns = _get_columns_by_type(
        statistical_profile,
        "numeric",
    )

    recommendations = []

    for column_x, column_y in combinations(numeric_columns, 2):
        recommendations.append(
            {
                "rule_id": "NUMERIC_NUMERIC_SCATTER",
                "chart_type": "scatter_plot",
                "columns": [column_x, column_y],
                "reason": (
                    f"Both '{column_x}' and '{column_y}' are numeric, "
                    "so a scatter plot can show their relationship."
                ),
                "confidence": 0.90,
                "priority": "high",
            }
        )

    return recommendations


# ---------------------------------------------------------------------------
# 6. Line Chart
# ---------------------------------------------------------------------------

def recommend_line_charts(
    statistical_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Recommend line charts for datetime and numeric combinations."""

    datetime_columns = _get_columns_by_type(
        statistical_profile,
        "datetime",
    )

    numeric_columns = _get_columns_by_type(
        statistical_profile,
        "numeric",
    )

    recommendations = []

    for datetime_column in datetime_columns:
        for numeric_column in numeric_columns:
            recommendations.append(
                {
                    "rule_id": "DATETIME_NUMERIC_LINE",
                    "chart_type": "line_chart",
                    "columns": [
                        datetime_column,
                        numeric_column,
                    ],
                    "reason": (
                        f"'{datetime_column}' is datetime and "
                        f"'{numeric_column}' is numeric, so a line chart "
                        "can show how the numeric value changes over time."
                    ),
                    "confidence": 0.95,
                    "priority": "high",
                }
            )

    return recommendations


# ---------------------------------------------------------------------------
# 7. Grouped Bar Chart
# ---------------------------------------------------------------------------

def recommend_grouped_bar_charts(
    statistical_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Recommend grouped bar charts for categorical-numeric relationships."""

    categorical_columns = _get_columns_by_type(
        statistical_profile,
        "categorical",
    )

    numeric_columns = _get_columns_by_type(
        statistical_profile,
        "numeric",
    )

    recommendations = []

    for categorical_column in categorical_columns:
        unique_count = _get_unique_count(
            statistical_profile,
            categorical_column,
        )

        # Avoid producing unreadable charts for very high-cardinality
        # categorical variables.
        if 2 <= unique_count <= 20:
            for numeric_column in numeric_columns:
                recommendations.append(
                    {
                        "rule_id": "CATEGORICAL_NUMERIC_GROUPED_BAR",
                        "chart_type": "grouped_bar_chart",
                        "columns": [
                            categorical_column,
                            numeric_column,
                        ],
                        "reason": (
                            f"'{categorical_column}' has a manageable "
                            "number of categories and can be compared "
                            f"against numeric variable '{numeric_column}' "
                            "using grouped bars."
                        ),
                        "confidence": 0.85,
                        "priority": "medium",
                    }
                )

    return recommendations


# ---------------------------------------------------------------------------
# 8. Stacked Bar Chart
# ---------------------------------------------------------------------------

def recommend_stacked_bar_charts(
    statistical_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Recommend stacked bar charts for categorical pairs."""

    categorical_columns = _get_columns_by_type(
        statistical_profile,
        "categorical",
    )

    recommendations = []

    for column_x, column_y in combinations(categorical_columns, 2):

        unique_x = _get_unique_count(
            statistical_profile,
            column_x,
        )

        unique_y = _get_unique_count(
            statistical_profile,
            column_y,
        )

        if 2 <= unique_x <= 20 and 2 <= unique_y <= 10:
            recommendations.append(
                {
                    "rule_id": "CATEGORICAL_CATEGORICAL_STACKED_BAR",
                    "chart_type": "stacked_bar_chart",
                    "columns": [
                        column_x,
                        column_y,
                    ],
                    "reason": (
                        f"'{column_x}' and '{column_y}' are categorical "
                        "variables with manageable cardinality, so a "
                        "stacked bar chart can show their joint distribution."
                    ),
                    "confidence": 0.85,
                    "priority": "medium",
                }
            )

    return recommendations


# ---------------------------------------------------------------------------
# 9. 100% Stacked Bar Chart
# ---------------------------------------------------------------------------

def recommend_100_percent_stacked_bar_charts(
    statistical_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Recommend normalized stacked bar charts for categorical pairs."""

    categorical_columns = _get_columns_by_type(
        statistical_profile,
        "categorical",
    )

    recommendations = []

    for column_x, column_y in combinations(categorical_columns, 2):

        unique_x = _get_unique_count(
            statistical_profile,
            column_x,
        )

        unique_y = _get_unique_count(
            statistical_profile,
            column_y,
        )

        if 2 <= unique_x <= 20 and 2 <= unique_y <= 10:
            recommendations.append(
                {
                    "rule_id": "CATEGORICAL_CATEGORICAL_100_PERCENT",
                    "chart_type": "100_percent_stacked_bar_chart",
                    "columns": [
                        column_x,
                        column_y,
                    ],
                    "reason": (
                        f"'{column_x}' and '{column_y}' are categorical, "
                        "so a 100% stacked bar chart can compare the "
                        "proportional composition of categories."
                    ),
                    "confidence": 0.85,
                    "priority": "medium",
                }
            )

    return recommendations


# ---------------------------------------------------------------------------
# 10. Correlation Heatmap
# ---------------------------------------------------------------------------

def recommend_correlation_heatmaps(
    statistical_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Recommend correlation heatmaps for multiple numeric columns."""

    numeric_columns = _get_columns_by_type(
        statistical_profile,
        "numeric",
    )

    if len(numeric_columns) < 2:
        return []

    return [
        {
            "rule_id": "MULTIPLE_NUMERIC_CORRELATION",
            "chart_type": "correlation_heatmap",
            "columns": numeric_columns,
            "reason": (
                "Multiple numeric columns are available, so a correlation "
                "heatmap can provide an overview of relationships between "
                "numeric variables."
            ),
            "confidence": 0.95,
            "priority": "high",
        }
    ]


# ---------------------------------------------------------------------------
# 11. Missingness Bar Chart
# ---------------------------------------------------------------------------

def recommend_missingness_bar_charts(
    statistical_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Recommend a bar chart when missing values are present."""

    columns = statistical_profile.get("columns", {})

    missing_columns = [
        column_name
        for column_name, profile in columns.items()
        if profile.get("missing_count", 0) > 0
    ]

    if not missing_columns:
        return []

    return [
        {
            "rule_id": "MISSINGNESS_BAR",
            "chart_type": "missingness_bar_chart",
            "columns": missing_columns,
            "reason": (
                "Missing values are present, so a missingness bar chart "
                "can compare missing-value counts across columns."
            ),
            "confidence": 0.95,
            "priority": "high",
        }
    ]


# ---------------------------------------------------------------------------
# 12. Missingness Heatmap
# ---------------------------------------------------------------------------

def recommend_missingness_heatmaps(
    statistical_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Recommend a missingness heatmap when multiple columns contain nulls."""

    columns = statistical_profile.get("columns", {})

    missing_columns = [
        column_name
        for column_name, profile in columns.items()
        if profile.get("missing_count", 0) > 0
    ]

    if len(missing_columns) < 2:
        return []

    return [
        {
            "rule_id": "MULTIPLE_COLUMN_MISSINGNESS",
            "chart_type": "missingness_heatmap",
            "columns": missing_columns,
            "reason": (
                "Multiple columns contain missing values, so a missingness "
                "heatmap can reveal patterns of missingness across columns."
            ),
            "confidence": 0.90,
            "priority": "medium",
        }
    ]


# ---------------------------------------------------------------------------
# 13. Violin Plot
# ---------------------------------------------------------------------------

def recommend_violin_plots(
    statistical_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Recommend violin plots for sufficiently large numeric datasets."""

    numeric_columns = _get_columns_by_type(
        statistical_profile,
        "numeric",
    )

    row_count = _get_row_count(statistical_profile)

    if row_count < 20:
        return []

    recommendations = []

    for column in numeric_columns:
        recommendations.append(
            {
                "rule_id": "NUMERIC_VIOLIN",
                "chart_type": "violin_plot",
                "columns": [column],
                "reason": (
                    f"'{column}' is numeric and the dataset contains "
                    f"{row_count} rows, so a violin plot can show the "
                    "shape and spread of its distribution."
                ),
                "confidence": 0.85,
                "priority": "medium",
            }
        )

    return recommendations


# ---------------------------------------------------------------------------
# 14. QQ Plot
# ---------------------------------------------------------------------------

def recommend_qq_plots(
    statistical_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Recommend QQ plots for numeric columns."""

    numeric_columns = _get_columns_by_type(
        statistical_profile,
        "numeric",
    )

    row_count = _get_row_count(statistical_profile)

    if row_count < 20:
        return []

    recommendations = []

    for column in numeric_columns:
        recommendations.append(
            {
                "rule_id": "NUMERIC_QQ",
                "chart_type": "qq_plot",
                "columns": [column],
                "reason": (
                    f"'{column}' is numeric, so a QQ plot can help assess "
                    "how closely its distribution follows a theoretical "
                    "normal distribution."
                ),
                "confidence": 0.80,
                "priority": "low",
            }
        )

    return recommendations


# ---------------------------------------------------------------------------
# 15. Pair Plot
# ---------------------------------------------------------------------------

def recommend_pair_plots(
    statistical_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Recommend a pair plot when there are multiple numeric columns."""

    numeric_columns = _get_columns_by_type(
        statistical_profile,
        "numeric",
    )

    # Pair plots become difficult to interpret and expensive when there
    # are too many numeric variables.
    if not 2 <= len(numeric_columns) <= 8:
        return []

    return [
        {
            "rule_id": "MULTIPLE_NUMERIC_PAIR_PLOT",
            "chart_type": "pair_plot",
            "columns": numeric_columns,
            "reason": (
                f"{len(numeric_columns)} numeric columns are available, "
                "so a pair plot can provide a combined view of their "
                "pairwise relationships and distributions."
            ),
            "confidence": 0.85,
            "priority": "medium",
        }
    ]
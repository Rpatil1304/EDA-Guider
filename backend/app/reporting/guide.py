"""Generate a readable EDA guide from the preprocessing pipeline result."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _format_value(value: Any) -> str:
    """Convert values into readable Markdown text."""

    if value is None:
        return "None"

    if isinstance(value, list):
        if not value:
            return "None"

        return ", ".join(
            "<blank>" if item == "" else str(item)
            for item in value
        )

    if isinstance(value, dict):
        if not value:
            return "None"

        return str(value)

    return str(value)


def _format_number(value: Any, decimals: int = 4) -> str:
    """Format numeric values without unnecessary precision."""

    if value is None:
        return "None"

    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


def _status(result: dict) -> str:
    """Return human-readable pipeline status."""

    return (
        "Completed"
        if result.get("status") == "success"
        else "Stopped with errors"
    )


def _add_numeric_statistics(
    lines: list[str],
    statistical_profile: dict,
) -> None:
    """Add numeric-column statistics to the report."""

    numeric_columns = (
        statistical_profile.get("numeric_columns") or {}
    )

    lines.extend([
        "### Numeric columns",
        "",
    ])

    if not numeric_columns:
        lines.append("No eligible numeric columns were available.")
        lines.append("")
        return

    lines.extend([
        "| Column | Count | Mean | Median | Std | Minimum | Maximum | Q1 | Q3 | Skewness | Kurtosis | Outliers | Outlier % |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])

    for column, stats in numeric_columns.items():

        lines.append(
            f"| {column} "
            f"| {_format_value(stats.get('count'))} "
            f"| {_format_number(stats.get('mean'))} "
            f"| {_format_number(stats.get('median'))} "
            f"| {_format_number(stats.get('std'))} "
            f"| {_format_number(stats.get('minimum'))} "
            f"| {_format_number(stats.get('maximum'))} "
            f"| {_format_number(stats.get('q1'))} "
            f"| {_format_number(stats.get('q3'))} "
            f"| {_format_number(stats.get('skewness'))} "
            f"| {_format_number(stats.get('kurtosis'))} "
            f"| {_format_value(stats.get('outlier_count'))} "
            f"| {_format_number(stats.get('outlier_percentage'), 2)}% |"
        )

    lines.append("")

    lines.extend([
        "#### IQR-based outlier bounds",
        "",
        "| Column | IQR | Lower bound | Upper bound | Outlier count | Outlier % |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ])

    for column, stats in numeric_columns.items():

        lines.append(
            f"| {column} "
            f"| {_format_number(stats.get('iqr'))} "
            f"| {_format_number(stats.get('lower_bound'))} "
            f"| {_format_number(stats.get('upper_bound'))} "
            f"| {_format_value(stats.get('outlier_count'))} "
            f"| {_format_number(stats.get('outlier_percentage'), 2)}% |"
        )

    lines.append("")


def _add_categorical_statistics(
    lines: list[str],
    statistical_profile: dict,
) -> None:
    """Add categorical-column statistics to the report."""

    categorical_columns = (
        statistical_profile.get("categorical_columns") or {}
    )

    lines.extend([
        "### Categorical columns",
        "",
    ])

    if not categorical_columns:
        lines.append("No eligible categorical columns were available.")
        lines.append("")
        return

    lines.extend([
        "| Column | Count | Unique | Top category | Top frequency | Top % |",
        "| --- | ---: | ---: | --- | ---: | ---: |",
    ])

    for column, stats in categorical_columns.items():

        lines.append(
            f"| {column} "
            f"| {_format_value(stats.get('count'))} "
            f"| {_format_value(stats.get('unique_count'))} "
            f"| {_format_value(stats.get('top'))} "
            f"| {_format_value(stats.get('top_frequency'))} "
            f"| {_format_number(stats.get('top_percentage'), 2)}% |"
        )

    lines.append("")

    lines.extend([
        "#### Top categories",
        "",
    ])

    for column, stats in categorical_columns.items():

        lines.append(
            f"**{column}**"
        )
        lines.append("")

        top_categories = (
            stats.get("top_categories") or {}
        )

        if not top_categories:
            lines.append("No category frequencies available.")
            lines.append("")
            continue

        lines.extend([
            "| Category | Frequency |",
            "| --- | ---: |",
        ])

        for category, frequency in top_categories.items():
            lines.append(
                f"| {category} | {frequency} |"
            )

        lines.append("")


def _add_datetime_statistics(
    lines: list[str],
    statistical_profile: dict,
) -> None:
    """Add datetime-column statistics to the report."""

    datetime_columns = (
        statistical_profile.get("datetime_columns") or {}
    )

    lines.extend([
        "### Datetime columns",
        "",
    ])

    if not datetime_columns:
        lines.append("No eligible datetime columns were available.")
        lines.append("")
        return

    lines.extend([
        "| Column | Count | Minimum | Maximum | Unique | Duration (days) |",
        "| --- | ---: | --- | --- | ---: | ---: |",
    ])

    for column, stats in datetime_columns.items():

        lines.append(
            f"| {column} "
            f"| {_format_value(stats.get('count'))} "
            f"| {_format_value(stats.get('minimum'))} "
            f"| {_format_value(stats.get('maximum'))} "
            f"| {_format_value(stats.get('unique_count'))} "
            f"| {_format_number(stats.get('duration_days'), 2)} |"
        )

    lines.append("")


def _add_boolean_statistics(
    lines: list[str],
    statistical_profile: dict,
) -> None:
    """Add boolean-column statistics to the report."""

    boolean_columns = (
        statistical_profile.get("boolean_columns") or {}
    )

    lines.extend([
        "### Boolean columns",
        "",
    ])

    if not boolean_columns:
        lines.append("No eligible boolean columns were available.")
        lines.append("")
        return

    lines.extend([
        "| Column | Count | True | True % | False | False % |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ])

    for column, stats in boolean_columns.items():

        lines.append(
            f"| {column} "
            f"| {_format_value(stats.get('count'))} "
            f"| {_format_value(stats.get('true_count'))} "
            f"| {_format_number(stats.get('true_percentage'), 2)}% "
            f"| {_format_value(stats.get('false_count'))} "
            f"| {_format_number(stats.get('false_percentage'), 2)}% |"
        )

    lines.append("")


def _add_correlations(
    lines: list[str],
    statistical_profile: dict,
) -> None:
    """Add numeric correlation matrix to the report."""

    correlation_matrix = (
        statistical_profile.get("correlation_matrix") or {}
    )

    lines.extend([
        "### Numeric correlation matrix",
        "",
    ])

    if not correlation_matrix:
        lines.append(
            "Correlation analysis requires at least two eligible numeric columns."
        )
        lines.append("")
        return

    columns = list(correlation_matrix.keys())

    header = "| Column | " + " | ".join(columns) + " |"
    separator = "| --- | " + " | ".join(
        ["---:"] * len(columns)
    ) + " |"

    lines.append(header)
    lines.append(separator)

    for column in columns:

        row_values = []

        for other_column in columns:

            value = (
                correlation_matrix
                .get(column, {})
                .get(other_column)
            )

            row_values.append(
                _format_number(value, 4)
            )

        lines.append(
            f"| {column} | "
            + " | ".join(row_values)
            + " |"
        )

    lines.append("")


def _add_column_overview(
    lines: list[str],
    statistical_profile: dict,
) -> None:
    """Add general statistics for every eligible column."""

    columns = (
        statistical_profile.get("columns") or {}
    )

    lines.extend([
        "### Eligible column overview",
        "",
    ])

    if not columns:
        lines.append("No eligible columns were available.")
        lines.append("")
        return

    lines.extend([
        "| Column | Semantic type | Count | Missing | Missing % | Unique | Unique % |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ])

    for column, stats in columns.items():

        lines.append(
            f"| {column} "
            f"| {_format_value(stats.get('inferred_type'))} "
            f"| {_format_value(stats.get('count'))} "
            f"| {_format_value(stats.get('missing_count'))} "
            f"| {_format_number(stats.get('missing_percentage'), 2)}% "
            f"| {_format_value(stats.get('unique_count'))} "
            f"| {_format_number(stats.get('unique_percentage'), 2)}% |"
        )

    lines.append("")


def generate_eda_guide_report(
    result: dict,
    output_path: str | Path | None = None,
) -> str:
    """Create a Markdown report for the completed EDA-guidance stages.

    The function only reads the structured pipeline result. It does not
    change the dataset or run the pipeline again.
    """

    if not isinstance(result, dict):
        raise TypeError(
            "result must be a pipeline result dictionary."
        )

    ingestion = result.get(
        "ingestion_report"
    ) or {}

    structural = result.get(
        "structural_report"
    ) or {}

    raw_profile = result.get(
        "raw_profile_report"
    ) or {}

    plan = result.get(
        "preprocessing_plan"
    ) or {}

    execution_log = result.get(
        "execution_log"
    ) or []

    summary_report = result.get(
        "preprocessing_summary_report"
    ) or {}

    summary = summary_report.get(
        "summary"
    ) or {}

    null_summary = raw_profile.get(
        "null_summary"
    ) or {}

    statistical_profile = result.get(
    "statistical_profile"
)

    if statistical_profile is not None:
        statistical_profile = statistical_profile.model_dump()

    file_name = ingestion.get(
        "file_name"
    ) or "Uploaded dataset"

    lines = [
        "# EDA-Guider Report",
        "",
        f"Dataset: **{file_name}**",
        f"Pipeline status: **{_status(result)}**",
        "",
        "## How to use this report",
        "",
        "Follow the completed sections from top to bottom. Each section explains "
        "what EDA-Guider checked, what it found, and what the user should know "
        "before continuing the analysis.",
        "",
        "## Part 1 - File ingestion",
        "",
        "The file was loaded without changing the original file.",
        "",
        f"- File type: {_format_value(ingestion.get('file_type'))}",
        f"- Encoding: {_format_value(ingestion.get('encoding'))}",
        f"- Delimiter: {_format_value(ingestion.get('delimiter'))}",
        f"- Header detected: {_format_value(ingestion.get('header_present'))}",
        f"- Rows: {_format_value(ingestion.get('rows'))}",
        f"- Columns: {_format_value(ingestion.get('columns'))}",
        "",
        "## Part 2 - Structure validation",
        "",
        "The dataset structure was checked before analysis.",
        "",
        f"- Validation status: {_format_value(structural.get('status'))}",
        f"- Duplicate columns: {_format_value(structural.get('duplicate_columns'))}",
        f"- Warnings: {_format_value(structural.get('warnings'))}",
        f"- Errors: {_format_value(structural.get('errors'))}",
        f"- Index-like columns retained for review: {_format_value(structural.get('index_like_columns'))}",
        "",
        "## Part 3 - Raw data profile",
        "",
        "This section describes the original values before preprocessing.",
        "",
        f"- Rows profiled: {_format_value(raw_profile.get('row_count'))}",
        f"- Columns profiled: {_format_value(raw_profile.get('column_count'))}",
        f"- Profile warnings: {len(raw_profile.get('warnings', []))}",
        "",
        "### Missing-value report",
        "",
        f"- Total cells: {_format_value(null_summary.get('total_cells'))}",
        f"- Actual null values: {_format_value(null_summary.get('actual_null_count'))} "
        f"({_format_value(null_summary.get('actual_null_percentage'))}%)",
        f"- Null-like text values: {_format_value(null_summary.get('null_like_count'))} "
        f"({_format_value(null_summary.get('null_like_percentage'))}%)",
        f"- Total missing values: {_format_value(null_summary.get('total_missing_count'))} "
        f"({_format_value(null_summary.get('total_missing_percentage'))}%)",
        f"- Columns with actual nulls: {_format_value(null_summary.get('columns_with_nulls'))}",
        f"- Columns with null-like values: {_format_value(null_summary.get('columns_with_null_like_values'))}",
        f"- Empty strings: {_format_value(null_summary.get('empty_string_count'))} "
        f"({_format_value(null_summary.get('empty_string_percentage'))}%)",
        f"- Whitespace-only strings: {_format_value(null_summary.get('whitespace_only_count'))} "
        f"({_format_value(null_summary.get('whitespace_only_percentage'))}%)",
        f"- Null-like marker breakdown: {_format_value(null_summary.get('null_like_breakdown'))}",
        f"- Columns with empty strings: {_format_value(null_summary.get('columns_with_empty_strings'))}",
        f"- Columns with whitespace-only strings: {_format_value(null_summary.get('columns_with_whitespace_only_values'))}",
        "",
        "Raw null and null-like values are reported and preserved. They are not "
        "automatically filled, deleted, or replaced.",
        "",
        "### Column profile",
        "",
        "| Column | Type | Semantic type | Confidence | Nulls | Unique | Numeric % | Datetime % | Boolean % | Outliers | Skewness |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for column in raw_profile.get("columns", []):
        lines.append(
            f"| {column.get('name')} | {column.get('dtype')} | "
            f"{column.get('semantic_type')} | "
            f"{column.get('classification_confidence', 0)} | "
            f"{column.get('null_count', 0)} "
            f"({column.get('null_percentage', 0)}%) | "
            f"{column.get('unique_count', 0)} | "
            f"{column.get('numeric_like_percentage', 0)} | "
            f"{column.get('datetime_like_percentage', 0)} | "
            f"{column.get('boolean_like_percentage', 0)} | "
            f"{column.get('outlier_count', 0)} | "
            f"{column.get('skewness')} |"
        )

    lines.extend([
        "",
        "## Part 4 - Preprocessing plan",
        "",
        "The rule engine created actions from the raw profile. These actions are "
        "recommendations for safe internal preparation, not changes to the original file.",
        "",
    ])

    actions = plan.get("actions", [])

    if actions:

        lines.append(
            "| Columns | Action | Confidence | Reason |"
        )
        lines.append(
            "| --- | --- | ---: | --- |"
        )

        for action in actions:

            confidence = round(
                float(
                    action.get(
                        "confidence",
                        0,
                    )
                ) * 100,
                2,
            )

            lines.append(
                f"| {_format_value(action.get('columns'))} | "
                f"{action.get('action')} | "
                f"{confidence}% | "
                f"{action.get('reason', '')} |"
            )

    else:
        lines.append(
            "No preprocessing actions were required."
        )

    lines.extend([
        "",
        "## Part 5 - Internal execution",
        "",
        "The planned safe actions were applied only to an internal copy. The "
        "uploaded source file was not modified.",
        "",
        f"- Execution log entries: {len(execution_log)}",
        f"- Action status counts: {_format_value(summary.get('action_status_counts'))}",
        "",
        "| Columns | Action | Status | Reason |",
        "| --- | --- | --- | --- |",
    ])

    for entry in execution_log:

        lines.append(
            f"| {_format_value(entry.get('columns'))} | "
            f"{entry.get('action')} | "
            f"{entry.get('status')} | "
            f"{entry.get('reason', '')} |"
        )

    lines.extend([
        "",
        "## Part 6 - Before-and-after summary",
        "",
        "The cleaned internal copy was profiled again and compared with the raw profile.",
        "",
        f"- Raw shape: {_format_value(summary.get('raw_row_count'))} rows x "
        f"{_format_value(summary.get('raw_column_count'))} columns",
        f"- Cleaned shape: {_format_value(summary.get('cleaned_row_count'))} rows x "
        f"{_format_value(summary.get('cleaned_column_count'))} columns",
        f"- Changed columns: {_format_value(summary.get('changed_column_count'))}",
        f"- Cleaned missing values: {_format_value((summary_report.get('cleaned_profile') or {}).get('null_summary', {}).get('total_missing_count'))}",
        f"- Excluded columns: {_format_value(summary.get('excluded_column_count'))}",
        f"- Unresolved columns: {_format_value(summary_report.get('unresolved_columns'))}",
        f"- Needs-review columns: {_format_value(summary_report.get('needs_review_columns'))}",
        f"- Raw snapshot unchanged: {_format_value(summary_report.get('raw_snapshot_unchanged'))}",
        "- Exclusion reasons: " + _format_value([
            f"{item.get('column')}: {'; '.join(item.get('reasons', []))}"
            for item in summary_report.get('excluded_columns', [])
        ]),
        "",
        "### Downstream handoff",
        "",
        f"- Eligible analysis columns: {_format_value((summary_report.get('downstream_handoff') or {}).get('eligible_columns'))}",
        f"- Sampling metadata: {_format_value((summary_report.get('downstream_handoff') or {}).get('sampling'))}",
        "",
    ])

    # -----------------------------------------------------------------------
    # Part 7 - Statistical analysis
    # -----------------------------------------------------------------------

    lines.extend([
        "## Part 7 - Statistical Analysis",
        "",
    ])

    if not statistical_profile:

        lines.extend([
            "Statistical profiling was not completed.",
            "",
            "The pipeline did not produce a statistical profile for this run.",
            "",
        ])

    else:

        lines.extend([
            "Statistical analysis was calculated locally from the internally "
            "cleaned dataset. Only columns marked as eligible by the existing "
            "downstream handoff were analyzed.",
            "",
            f"- Rows analyzed: {_format_value(statistical_profile.get('n_rows'))}",
            f"- Columns in cleaned dataset: {_format_value(statistical_profile.get('n_cols'))}",
            "",
        ])

        _add_column_overview(
            lines,
            statistical_profile,
        )

        _add_numeric_statistics(
            lines,
            statistical_profile,
        )

        _add_categorical_statistics(
            lines,
            statistical_profile,
        )

        _add_datetime_statistics(
            lines,
            statistical_profile,
        )

        _add_boolean_statistics(
            lines,
            statistical_profile,
        )

        _add_correlations(
            lines,
            statistical_profile,
        )

        lines.extend([
            "### Statistical analysis note",
            "",
            "The statistics above are computed evidence, not LLM-generated "
            "interpretations. Columns excluded or marked for review during "
            "preprocessing are not included in the eligible downstream analysis.",
            "",
        ])

    lines.extend([
        "## Part 8 - Next EDA steps",
        "",
        "The next stages will use the statistical evidence above to provide:",
        "",
        "1. Deterministic visualization recommendations",
        "2. Evidence-based insight generation",
        "3. Final EDA guidance",
        "",
        "The visualization recommendation stage will remain rule-based, while "
        "future LLM usage will be restricted to reasoning over structured "
        "privacy-safe evidence.",
        "",
    ])

    report = "\n".join(lines)

    if output_path is not None:
        Path(output_path).write_text(
            report,
            encoding="utf-8",
        )

    return report
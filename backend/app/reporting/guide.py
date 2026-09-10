"""Generate a readable EDA guide from the preprocessing pipeline result."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _format_value(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "None"
    return str(value)


def _status(result: dict) -> str:
    return "Completed" if result.get("status") == "success" else "Stopped with errors"


def generate_eda_guide_report(
    result: dict,
    output_path: str | Path | None = None,
) -> str:
    """Create a Markdown report for the completed EDA-guidance stages.

    The function only reads the structured pipeline result. It does not change
    the dataset or run the pipeline again.
    """

    if not isinstance(result, dict):
        raise TypeError("result must be a pipeline result dictionary.")

    ingestion = result.get("ingestion_report") or {}
    structural = result.get("structural_report") or {}
    raw_profile = result.get("raw_profile_report") or {}
    plan = result.get("preprocessing_plan") or {}
    execution_log = result.get("execution_log") or []
    summary_report = result.get("preprocessing_summary_report") or {}
    summary = summary_report.get("summary") or {}
    null_summary = raw_profile.get("null_summary") or {}
    file_name = ingestion.get("file_name") or "Uploaded dataset"

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
        "",
        "Null and null-like values are reported, not automatically filled or "
        "replaced. They do not prevent later visualization or insight analysis.",
        "",
        "### Column profile",
        "",
        "| Column | Type | Nulls | Null-like values | Unique values |",
        "| --- | --- | ---: | ---: | ---: |",
    ]

    for column in raw_profile.get("columns", []):
        lines.append(
            f"| {column.get('name')} | {column.get('dtype')} | "
            f"{column.get('null_count', 0)} ({column.get('null_percentage', 0)}%) | "
            f"{column.get('null_like_count', 0)} | {column.get('unique_count', 0)} |"
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
        lines.append("| Columns | Action | Confidence | Reason |")
        lines.append("| --- | --- | ---: | --- |")
        for action in actions:
            confidence = round(float(action.get("confidence", 0)) * 100, 2)
            lines.append(
                f"| {_format_value(action.get('columns'))} | {action.get('action')} | "
                f"{confidence}% | {action.get('reason', '')} |"
            )
    else:
        lines.append("No preprocessing actions were required.")

    lines.extend([
        "",
        "## Part 5 - Internal execution",
        "",
        "The planned safe actions were applied only to an internal copy. The "
        "uploaded source file was not modified.",
        "",
        f"- Execution log entries: {len(execution_log)}",
        "",
        "| Columns | Action | Status | Reason |",
        "| --- | --- | --- | --- |",
    ])
    for entry in execution_log:
        lines.append(
            f"| {_format_value(entry.get('columns'))} | {entry.get('action')} | "
            f"{entry.get('status')} | {entry.get('reason', '')} |"
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
        "",
        "## Part 7 - Next EDA steps",
        "",
        "This stage is planned for the next version. It will use the prepared "
        "internal data and the evidence above to provide:",
        "",
        "1. Statistical analysis",
        "2. Visualization recommendations",
        "3. Evidence-based insights",
        "",
        "Until Part 7 is implemented, use this report to review data quality, "
        "understand preprocessing decisions, and decide what analysis should be performed next.",
        "",
    ])

    report = "\n".join(lines)
    if output_path is not None:
        Path(output_path).write_text(report, encoding="utf-8")
    return report
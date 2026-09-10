"""Post-cleaning profile comparison and preprocessing summary reports."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pandas as pd

from app.profiling.raw_profiler import profile_raw_dataframe


_COMPARE_FIELDS = ("dtype", "null_percentage", "unique_count")


def _column_key(name: Any) -> str:
    return str(name)


def _profile_with_kind(df: pd.DataFrame, kind: str) -> dict:
    profile = profile_raw_dataframe(df)
    profile["profile_type"] = kind
    return profile


def build_preprocessing_summary_report(
    raw_profile_report: dict,
    cleaned_dataframe: pd.DataFrame,
    execution_log: list[dict],
) -> dict:
    """Build the final Part 6 artifact from raw and cleaned pipeline outputs.

    The cleaned profile uses the same profiling function as Part 3. Column
    comparisons are positional so duplicate raw names remain traceable after
    structural normalization has assigned unique cleaned names.
    """

    if not isinstance(cleaned_dataframe, pd.DataFrame):
        raise TypeError("cleaned_dataframe must be a pandas DataFrame.")
    if raw_profile_report.get("profile_type") != "raw":
        raise ValueError("raw_profile_report must be a raw profile report.")
    if not isinstance(execution_log, list):
        raise TypeError("execution_log must be a list of log entries.")

    cleaned_profile = _profile_with_kind(cleaned_dataframe, "cleaned")
    raw_columns = raw_profile_report.get("columns", [])
    cleaned_columns = cleaned_profile.get("columns", [])
    column_count = max(len(raw_columns), len(cleaned_columns))
    column_summaries: list[dict] = []

    for index in range(column_count):
        before = deepcopy(raw_columns[index]) if index < len(raw_columns) else None
        after = deepcopy(cleaned_columns[index]) if index < len(cleaned_columns) else None
        before_name = before.get("name") if before else None
        after_name = after.get("name") if after else None
        related_logs = [
            deepcopy(entry)
            for entry in execution_log
            if before_name in entry.get("columns", [])
            or after_name in entry.get("columns", [])
        ]
        changes: dict[str, dict[str, Any]] = {}
        for field in _COMPARE_FIELDS:
            before_value = before.get(field) if before else None
            after_value = after.get(field) if after else None
            changes[field] = {
                "before": before_value,
                "after": after_value,
                "changed": before_value != after_value,
            }

        column_summaries.append(
            {
                "position": index,
                "column_before": before_name,
                "column_after": after_name,
                "before": before,
                "actions": related_logs,
                "changes": changes,
                "after": after,
            }
        )

    changed_columns = [
        summary["column_after"] or summary["column_before"]
        for summary in column_summaries
        if any(change["changed"] for change in summary["changes"].values())
        or summary["actions"]
    ]

    return {
        "report_type": "preprocessing_summary",
        "raw_profile": deepcopy(raw_profile_report),
        "cleaned_profile": cleaned_profile,
        "null_summary": deepcopy(raw_profile_report.get("null_summary", {})),
        "execution_log": deepcopy(execution_log),
        "columns": column_summaries,
        "summary": {
            "raw_row_count": raw_profile_report.get("row_count", 0),
            "cleaned_row_count": cleaned_profile.get("row_count", 0),
            "raw_column_count": raw_profile_report.get("column_count", 0),
            "cleaned_column_count": cleaned_profile.get("column_count", 0),
            "changed_column_count": len(set(changed_columns)),
            "execution_log_count": len(execution_log),
        },
    }


def run_preprocessing_stage(
    dataframe: pd.DataFrame,
    raw_profile_report: dict,
    preprocessing_plan,
    data_loss_threshold: float = 0.30,
    case_strategy: str = "lower",
) -> tuple[pd.DataFrame, dict]:
    """Execute Part 5 and return the cleaned data plus final Part 6 report."""

    from app.preprocessing.preprocessor import execute_preprocessing_plan

    cleaned_dataframe, execution_log = execute_preprocessing_plan(
        dataframe,
        preprocessing_plan,
        data_loss_threshold=data_loss_threshold,
        case_strategy=case_strategy,
    )
    summary = build_preprocessing_summary_report(
        raw_profile_report,
        cleaned_dataframe,
        execution_log,
    )
    return cleaned_dataframe, summary


# Alias matching the requested artifact name.
generate_preprocessing_summary = build_preprocessing_summary_report

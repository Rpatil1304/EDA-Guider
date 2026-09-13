"""Structural validation and safe normalization for loaded tabular data."""

from __future__ import annotations

from collections import defaultdict
import re

import pandas as pd


def _normalize_column_name(value: object, position: int) -> str:
    name = str(value).strip()
    if not name or name.lower().startswith("unnamed:"):
        name = f"column_{position + 1}"
    name = re.sub(r"[^0-9A-Za-z]+", "_", name).strip("_").lower()
    return name or f"column_{position + 1}"


def _unique_column_names(columns: pd.Index) -> tuple[list[object], list[dict]]:
    """Return unique names while preserving the original column order."""

    used: set[object] = set()
    counts: defaultdict[object, int] = defaultdict(int)
    renamed: list[object] = []
    changes: list[dict] = []

    for original in columns:
        candidate = original
        counts[original] += 1
        occurrence = counts[original]

        if candidate in used:
            suffix = occurrence
            candidate = f"{original}_{suffix}"
            while candidate in used:
                suffix += 1
                candidate = f"{original}_{suffix}"
            changes.append(
                {
                    "original": original,
                    "new": candidate,
                    "reason": "Duplicate column name was renamed with a suffix.",
                }
            )

        used.add(candidate)
        renamed.append(candidate)

    return renamed, changes


def validate_structure(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame | None, dict]:
    """Validate and safely normalize the basic structure of a DataFrame.

    Returns a copied DataFrame and a structured report. Fatal structural
    problems return ``None`` and are recorded in ``errors``. Duplicate column
    names are auto-renamed; single-row and single-column datasets continue with
    warnings because they may still be valid inputs for downstream inspection.
    """

    report = {
        "status": "error",
        "fatal": False,
        "row_count": 0,
        "column_count": 0,
        "duplicate_columns": [],
        "renamed_columns": [],
        "warnings": [],
        "errors": [],
        "duplicate_value_columns": [],
        "normalized_columns": [],
    }

    if not isinstance(df, pd.DataFrame):
        report["fatal"] = True
        report["errors"].append(
            {
                "type": "TypeError",
                "message": "Structural validation requires a pandas DataFrame.",
            }
        )
        return None, report

    report["row_count"] = len(df)
    report["column_count"] = len(df.columns)

    if len(df.columns) == 0:
        report["fatal"] = True
        report["errors"].append(
            {
                "type": "EmptyStructureError",
                "message": "The dataset contains zero columns.",
            }
        )
        return None, report

    if len(df) == 0:
        report["fatal"] = True
        report["errors"].append(
            {
                "type": "EmptyStructureError",
                "message": "The dataset contains zero rows.",
            }
        )
        return None, report

    duplicate_mask = df.columns.duplicated(keep=False)
    report["duplicate_columns"] = list(dict.fromkeys(df.columns[duplicate_mask]))
    normalized = df.copy()

    duplicate_value_columns = []
    for left_index, left_name in enumerate(normalized.columns):
        for right_index in range(left_index + 1, len(normalized.columns)):
            if normalized.iloc[:, left_index].equals(normalized.iloc[:, right_index]):
                duplicate_value_columns.append(
                    [str(left_name), str(normalized.columns[right_index])]
                )
    report["duplicate_value_columns"] = duplicate_value_columns
    if duplicate_value_columns:
        report["warnings"].append(
            "Columns with identical values were retained for review."
        )

    if report["duplicate_columns"]:
        new_columns, changes = _unique_column_names(normalized.columns)
        normalized.columns = new_columns
        report["renamed_columns"] = changes
        report["warnings"].append(
            "Duplicate column names were renamed with deterministic suffixes."
        )

    original_columns = list(normalized.columns)
    original_index_names = {
        index: str(column).strip().lower()
        for index, column in enumerate(original_columns)
    }
    normalized.columns = [
        _normalize_column_name(column, index)
        for index, column in enumerate(normalized.columns)
    ]
    report["normalized_columns"] = [
        {"original": str(before), "new": after}
        for before, after in zip(original_columns, normalized.columns)
        if str(before) != after
    ]
    normalized.columns, normalization_changes = _unique_column_names(normalized.columns)
    report["renamed_columns"].extend(normalization_changes)

    index_like_columns = [
        str(original_columns[index])
        for index, column in enumerate(normalized.columns)
        if original_index_names[index] in {"", "unnamed: 0", "index"}
        and pd.api.types.is_numeric_dtype(normalized[column])
        and normalized[column].reset_index(drop=True).equals(
            pd.Series(range(len(normalized)), index=normalized.index)
        )
    ]
    if index_like_columns:
        report["warnings"].append(
            "Index-like columns were detected and retained for review: "
            + ", ".join(index_like_columns)
        )
    report["index_like_columns"] = index_like_columns

    if len(normalized) == 1:
        report["warnings"].append(
            "The dataset contains only one row; statistical conclusions may be limited."
        )
    elif len(normalized) < 5:
        report["warnings"].append(
            "The dataset has fewer than 5 rows; statistical conclusions may be unstable."
        )

    if len(normalized.columns) == 1:
        report["warnings"].append(
            "The dataset contains only one column; relationship analysis may be limited."
        )

    report["status"] = "success"
    return normalized, report

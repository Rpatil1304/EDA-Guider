"""Structural validation and safe normalization for loaded tabular data."""

from __future__ import annotations

from collections import defaultdict

import pandas as pd


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

    if report["duplicate_columns"]:
        new_columns, changes = _unique_column_names(normalized.columns)
        normalized.columns = new_columns
        report["renamed_columns"] = changes
        report["warnings"].append(
            "Duplicate column names were renamed with deterministic suffixes."
        )

    index_like_columns = [
        str(column)
        for column in normalized.columns
        if str(column).strip().lower() in {"", "unnamed: 0", "index"}
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

    if len(normalized.columns) == 1:
        report["warnings"].append(
            "The dataset contains only one column; relationship analysis may be limited."
        )

    report["status"] = "success"
    return normalized, report

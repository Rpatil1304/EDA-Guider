"""Lightweight, non-mutating profiling for raw ingested DataFrames."""

from __future__ import annotations

from typing import Any
import re

import pandas as pd


_HIGH_CARDINALITY_RATIO = 0.90
_HIGH_CORRELATION_THRESHOLD = 0.95
_HIGH_MISSING_RATIO = 0.50
_SAMPLE_SIZE = 5
_NULL_LIKE_VALUES = {"", "na", "n/a", "nan", "null", "none", "missing"}
_BOOLEAN_VALUES = {"true", "false", "yes", "no", "y", "n", "1", "0"}
_NUMERIC_PATTERN = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
_ID_NAME_PATTERN = re.compile(
    r"(^|[_\s-])(id|uuid|guid|identifier|code|account_number|reference_number)($|[_\s-])",
    re.IGNORECASE,
)


def _json_safe(value: Any) -> Any:
    """Convert common pandas and NumPy values to report-safe Python values."""

    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, TypeError):
            pass
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except (ValueError, TypeError):
            pass
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _column_profile(series: pd.Series, row_count: int) -> dict:
    """Collect requested metrics for one raw column without changing it."""

    null_count = int(series.isna().sum())
    unique_count = int(series.nunique(dropna=True))
    sample_values = [
        _json_safe(value)
        for value in series.dropna().head(_SAMPLE_SIZE).tolist()
    ]
    null_percentage = (null_count / row_count * 100) if row_count else 0.0
    unique_ratio = (unique_count / row_count) if row_count else 0.0
    values = series.dropna()
    string_values = values[values.map(lambda value: isinstance(value, str))]
    string_count = len(string_values)
    null_like_count = int(
        series.map(
            lambda value: isinstance(value, str)
            and value.strip().lower() in _NULL_LIKE_VALUES
        ).sum()
    )
    null_like_breakdown = {
        marker: int(
            series.map(
                lambda value: isinstance(value, str)
                and value.strip().lower() == marker
            ).sum()
        )
        for marker in sorted(_NULL_LIKE_VALUES)
    }
    whitespace_count = int(
        sum(value != value.strip() for value in string_values.tolist())
    )
    empty_string_count = int(
        sum(value.strip() == "" for value in string_values.tolist())
    )
    non_null_count = len(values)
    numeric_like_count = int(
        sum(
            bool(_NUMERIC_PATTERN.match(value.strip()))
            for value in string_values.tolist()
        )
    )
    datetime_like_count = 0
    if not pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
        parsed_datetimes = pd.to_datetime(
            values,
            errors="coerce",
            format="mixed",
        )
        datetime_like_count = int(
            pd.Series(parsed_datetimes).notna().sum()
        )
    boolean_like_count = int(
        sum(
            isinstance(value, bool)
            or (isinstance(value, str) and value.strip().lower() in _BOOLEAN_VALUES)
            or (isinstance(value, (int, float)) and value in (0, 1))
            for value in values.tolist()
        )
    )
    variable_length = (
        string_values.map(len).nunique() > 1 if string_count else False
    )
    id_name_signal = bool(_ID_NAME_PATTERN.search(str(series.name)))

    warnings: list[str] = []
    if null_percentage >= _HIGH_MISSING_RATIO * 100:
        warnings.append("High missingness: at least 50% of values are null.")
    if row_count and unique_ratio >= _HIGH_CARDINALITY_RATIO and unique_count > 1:
        warnings.append("High cardinality: at least 90% of rows have unique values.")
    if unique_count <= 1:
        warnings.append("Constant or entirely null column.")

    return {
        "name": str(series.name),
        "dtype": str(series.dtype),
        "null_count": null_count,
        "null_percentage": round(null_percentage, 4),
        "unique_count": unique_count,
        "sample_values": sample_values,
        "null_like_count": null_like_count,
        "null_like_breakdown": null_like_breakdown,
        "whitespace_count": whitespace_count,
        "empty_string_count": empty_string_count,
        "numeric_like_percentage": round(
            numeric_like_count / non_null_count * 100, 4
        ) if non_null_count else 0.0,
        "datetime_like_percentage": round(
            datetime_like_count / non_null_count * 100, 4
        ) if non_null_count else 0.0,
        "boolean_like_percentage": round(
            boolean_like_count / non_null_count * 100, 4
        ) if non_null_count else 0.0,
        "is_likely_id": bool(
            row_count > 1
            and unique_ratio >= _HIGH_CARDINALITY_RATIO
            and id_name_signal
        ),
        "is_categorical": bool(
            row_count > 0 and unique_ratio <= 0.20 and unique_count > 1
        ),
        "is_free_text": bool(
            string_count > 0 and unique_ratio >= _HIGH_CARDINALITY_RATIO
            and variable_length
        ),
        "warnings": warnings,
    }


def _correlation_warnings(df: pd.DataFrame) -> list[dict]:
    """Find highly correlated numeric column pairs without modifying ``df``."""

    numeric = df.select_dtypes(include="number")
    if numeric.shape[1] < 2:
        return []

    correlations = numeric.corr(method="pearson", numeric_only=True)
    warnings: list[dict] = []
    for index, first in enumerate(range(len(correlations.columns))):
        for second in range(index + 1, len(correlations.columns)):
            value = correlations.iloc[first, second]
            if pd.notna(value) and abs(float(value)) >= _HIGH_CORRELATION_THRESHOLD:
                warnings.append(
                    {
                        "type": "high_correlation",
                        "columns": [
                            str(numeric.columns[first]),
                            str(numeric.columns[second]),
                        ],
                        "correlation": round(float(value), 4),
                        "message": (
                            "Numeric columns have an absolute Pearson correlation "
                            "of at least 0.95."
                        ),
                    }
                )
    return warnings


def profile_raw_dataframe(df: pd.DataFrame) -> dict:
    """Return a structured profile of the raw DataFrame.

    The input is only read; it is never cleaned, coerced, or otherwise
    modified. The returned report is independent and can be retained for later
    comparison with a cleaned-data profile.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Raw profiling requires a pandas DataFrame.")

    row_count = len(df)
    column_profiles = [
        _column_profile(df.iloc[:, index], row_count)
        for index in range(len(df.columns))
    ]
    warnings = [
        {
            "type": (
                "high_missingness"
                if message.startswith("High missingness")
                else "high_cardinality"
                if message.startswith("High cardinality")
                else "constant_column"
                if message.startswith("Constant")
                else "column_warning"
            ),
            "column": column_profile["name"],
            "message": message,
        }
        for column_profile in column_profiles
        for message in column_profile["warnings"]
    ]
    warnings.extend(_correlation_warnings(df))

    actual_null_count = sum(
        column_profile["null_count"] for column_profile in column_profiles
    )
    null_like_count = sum(
        column_profile["null_like_count"] for column_profile in column_profiles
    )
    total_cells = row_count * len(df.columns)
    columns_with_nulls = [
        column_profile["name"]
        for column_profile in column_profiles
        if column_profile["null_count"] > 0
    ]
    columns_with_null_like_values = [
        column_profile["name"]
        for column_profile in column_profiles
        if column_profile["null_like_count"] > 0
    ]

    return {
        "profile_type": "raw",
        "row_count": row_count,
        "column_count": len(df.columns),
        "columns": column_profiles,
        "null_summary": {
            "total_cells": total_cells,
            "actual_null_count": actual_null_count,
            "actual_null_percentage": round(
                actual_null_count / total_cells * 100, 4
            ) if total_cells else 0.0,
            "null_like_count": null_like_count,
            "null_like_percentage": round(
                null_like_count / total_cells * 100, 4
            ) if total_cells else 0.0,
            "total_missing_count": actual_null_count + null_like_count,
            "total_missing_percentage": round(
                (actual_null_count + null_like_count) / total_cells * 100, 4
            ) if total_cells else 0.0,
            "columns_with_nulls": columns_with_nulls,
            "columns_with_null_like_values": columns_with_null_like_values,
        },
        "warnings": warnings,
        "metadata": {
            "high_cardinality_threshold": _HIGH_CARDINALITY_RATIO,
            "high_correlation_threshold": _HIGH_CORRELATION_THRESHOLD,
            "high_missingness_threshold": _HIGH_MISSING_RATIO,
        },
    }


# Descriptive alias for callers that prefer the report-oriented name.
generate_raw_profile = profile_raw_dataframe

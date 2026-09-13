"""Lightweight, non-mutating profiling for raw ingested DataFrames."""

from __future__ import annotations

from typing import Any
import re

import pandas as pd

from app.profiling.parsing import numeric_parse_mask


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
_ISO_DATE_PATTERN = re.compile(r"^\d{4}[-/.]\d{1,2}[-/.]\d{1,2}$")
_NUMERIC_DATE_PATTERN = re.compile(r"^\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}$")
_NAMED_DATE_PATTERN = re.compile(r"[A-Za-z]{3,9}")
_UNIT_PATTERN = re.compile(r"[A-Za-z%²$€£₹]+")


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


def _format_signatures(string_values: pd.Series) -> set[str]:
    """Collect conservative date and unit-format signatures for review."""

    signatures: set[str] = set()
    for value in string_values.tolist():
        text = value.strip()
        if _ISO_DATE_PATTERN.fullmatch(text):
            signatures.add("iso_date")
        elif _NUMERIC_DATE_PATTERN.fullmatch(text):
            signatures.add("numeric_date")
        elif _NAMED_DATE_PATTERN.search(text) and any(
            marker in text.lower()
            for marker in ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")
        ):
            signatures.add("named_date")

        has_measurement_signal = bool(re.search(r"\d|[%$€£₹²]", text))
        if has_measurement_signal:
            units = _UNIT_PATTERN.findall(text)
            if units:
                signatures.add("unit:" + " ".join(sorted(unit.lower() for unit in units)))
            elif numeric_parse_mask(pd.Series([text])).iloc[0]:
                signatures.add("unit:none")
    return signatures


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
    non_null_types = {type(value).__name__ for value in values.tolist()}
    average_string_length = (
        float(string_values.map(len).mean()) if not string_values.empty else 0.0
    )
    lower_values = {
        value.strip().lower()
        for value in string_values.tolist()
        if value.strip()
    }
    case_variation = len(lower_values) < len(
        {value.strip() for value in string_values.tolist() if value.strip()}
    )
    format_signatures = _format_signatures(string_values)
    non_null_count = len(values)
    numeric_like_count = int(numeric_parse_mask(values).sum())
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
    index_like = (
        str(series.name).strip().lower() in {"", "unnamed: 0", "index"}
        and pd.api.types.is_numeric_dtype(series)
        and series.reset_index(drop=True).equals(pd.Series(range(row_count)))
    )

    warnings: list[str] = []
    if null_percentage >= _HIGH_MISSING_RATIO * 100:
        warnings.append("High missingness: at least 50% of values are null.")
    if row_count and unique_ratio >= _HIGH_CARDINALITY_RATIO and unique_count > 1:
        warnings.append("High cardinality: at least 90% of rows have unique values.")
    if unique_count <= 1:
        warnings.append("Constant or entirely null column.")

    outlier_count = 0
    skewness = None
    numeric_values = pd.to_numeric(values, errors="coerce")
    numeric_values = numeric_values.dropna()
    if len(numeric_values) >= 4:
        q1 = numeric_values.quantile(0.25)
        q3 = numeric_values.quantile(0.75)
        iqr = q3 - q1
        if iqr:
            outlier_count = int(
                ((numeric_values < q1 - 1.5 * iqr) | (numeric_values > q3 + 1.5 * iqr)).sum()
            )
        skewness = float(numeric_values.skew())
        if abs(skewness) >= 1:
            warnings.append("Heavily skewed numeric column.")

    if pd.api.types.is_numeric_dtype(series):
        semantic_type, classification_confidence = "numeric", 1.0
    elif pd.api.types.is_bool_dtype(series):
        semantic_type, classification_confidence = "boolean", 1.0
    elif numeric_like_count and numeric_like_count / max(1, non_null_count) >= 0.8:
        semantic_type, classification_confidence = "numeric", numeric_like_count / non_null_count
    elif datetime_like_count and datetime_like_count / max(1, non_null_count) >= 0.8:
        semantic_type, classification_confidence = "datetime", datetime_like_count / non_null_count
    elif boolean_like_count and boolean_like_count / max(1, non_null_count) >= 0.8:
        semantic_type, classification_confidence = "boolean", boolean_like_count / non_null_count
    elif id_name_signal and unique_ratio >= 0.9:
        semantic_type, classification_confidence = "identifier", unique_ratio
    elif unique_ratio <= 0.2 and unique_count > 1:
        semantic_type, classification_confidence = "categorical", 1.0 - unique_ratio
    elif string_count and unique_ratio >= 0.9 and variable_length:
        semantic_type, classification_confidence = "free_text", unique_ratio
    else:
        semantic_type, classification_confidence = "unresolved", 0.0

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
        "whitespace_only_count": int(
            sum(value.strip() == "" and value != "" for value in string_values.tolist())
        ),
        "average_string_length": round(average_string_length, 4),
        "uniqueness_ratio": round(unique_ratio, 4),
        "mixed_type_count": len(non_null_types),
        "has_mixed_types": len(non_null_types) > 1,
        "has_case_variations": case_variation,
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
        "is_index_like": bool(index_like),
        "is_categorical": bool(
            row_count > 0 and unique_ratio <= 0.20 and unique_count > 1
        ),
        "is_free_text": bool(
            string_count > 0 and unique_ratio >= _HIGH_CARDINALITY_RATIO
            and variable_length
        ),
        "semantic_type": semantic_type,
        "classification_confidence": round(float(classification_confidence), 4),
        "format_signatures": sorted(format_signatures),
        "mixed_format_warning": len(format_signatures) > 1,
        "outlier_count": outlier_count,
        "outlier_values": [
            _json_safe(value)
            for value in numeric_values[
                (numeric_values < numeric_values.quantile(0.25) - 1.5 * (numeric_values.quantile(0.75) - numeric_values.quantile(0.25)))
                | (numeric_values > numeric_values.quantile(0.75) + 1.5 * (numeric_values.quantile(0.75) - numeric_values.quantile(0.25)))
            ].tolist()
        ] if outlier_count else [],
        "skewness": round(skewness, 6) if skewness is not None else None,
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
    duplicate_value_pairs = []
    for left_index in range(len(df.columns)):
        for right_index in range(left_index + 1, len(df.columns)):
            if df.iloc[:, left_index].equals(df.iloc[:, right_index]):
                duplicate_value_pairs.append([
                    str(df.columns[left_index]), str(df.columns[right_index])
                ])
    duplicate_value_columns = {
        column
        for pair in duplicate_value_pairs
        for column in pair
    }
    for profile in column_profiles:
        profile["duplicate_value_column"] = profile["name"] in duplicate_value_columns
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
    empty_string_count = sum(
        column_profile["empty_string_count"] for column_profile in column_profiles
    )
    whitespace_only_count = sum(
        column_profile["whitespace_only_count"]
        for column_profile in column_profiles
    )
    null_like_breakdown = {
        marker: sum(
            column_profile["null_like_breakdown"].get(marker, 0)
            for column_profile in column_profiles
        )
        for marker in sorted(_NULL_LIKE_VALUES)
    }
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
    columns_with_empty_strings = [
        column_profile["name"]
        for column_profile in column_profiles
        if column_profile["empty_string_count"] > 0
    ]
    columns_with_whitespace_only_values = [
        column_profile["name"]
        for column_profile in column_profiles
        if column_profile["whitespace_only_count"] > 0
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
            "empty_string_count": empty_string_count,
            "empty_string_percentage": round(
                empty_string_count / total_cells * 100, 4
            ) if total_cells else 0.0,
            "whitespace_only_count": whitespace_only_count,
            "whitespace_only_percentage": round(
                whitespace_only_count / total_cells * 100, 4
            ) if total_cells else 0.0,
            "null_like_breakdown": null_like_breakdown,
            "columns_with_empty_strings": columns_with_empty_strings,
            "columns_with_whitespace_only_values": columns_with_whitespace_only_values,
        },
        "warnings": warnings,
        "duplicate_value_columns": duplicate_value_pairs,
        "metadata": {
            "high_cardinality_threshold": _HIGH_CARDINALITY_RATIO,
            "high_correlation_threshold": _HIGH_CORRELATION_THRESHOLD,
            "high_missingness_threshold": _HIGH_MISSING_RATIO,
        },
    }


# Descriptive alias for callers that prefer the report-oriented name.
generate_raw_profile = profile_raw_dataframe

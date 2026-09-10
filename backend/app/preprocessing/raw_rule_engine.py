"""Generate preprocessing proposals from the preserved raw profile."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.schemas.preprocessing import PreprocessingAction, PreprocessingPlan


def _confidence(percentage: float) -> float:
    return round(max(0.0, min(1.0, percentage / 100.0)), 4)


def _add_action(
    actions: list[PreprocessingAction],
    column: str,
    action: str,
    confidence: float,
    reason: str,
    parameters: dict[str, Any] | None = None,
) -> None:
    actions.append(
        PreprocessingAction(
            columns=[column],
            action=action,
            confidence=_confidence(confidence),
            parameters=parameters or {},
            reason=reason,
        )
    )


def generate_preprocessing_plan_from_raw_profile(
    df: pd.DataFrame,
    raw_profile: dict,
) -> PreprocessingPlan:
    """Create non-mutating preprocessing proposals from raw profile evidence.

    ``raw_profile`` must be produced by
    :func:`app.profiling.raw_profiler.profile_raw_dataframe`. Columns are
    matched by position so duplicate raw names remain safe after structural
    validation has assigned unique output names.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("A DataFrame is required to generate a preprocessing plan.")
    if raw_profile.get("profile_type") != "raw":
        raise ValueError("raw_profile must be a raw profile report.")

    actions: list[PreprocessingAction] = []
    profiles = raw_profile.get("columns", [])
    if len(profiles) != len(df.columns):
        raise ValueError("Raw profile columns do not match the DataFrame columns.")

    for index, profile in enumerate(profiles):
        column = str(df.columns[index])
        whitespace_count = profile.get("whitespace_count", 0)
        numeric_score = float(profile.get("numeric_like_percentage", 0.0))
        datetime_score = float(profile.get("datetime_like_percentage", 0.0))
        boolean_score = float(profile.get("boolean_like_percentage", 0.0))
        is_string_like = (
            pd.api.types.is_object_dtype(df.dtypes.iloc[index])
            or pd.api.types.is_string_dtype(df.dtypes.iloc[index])
        )
        unique_ratio = (
            profile.get("unique_count", 0) / raw_profile["row_count"]
            if raw_profile["row_count"]
            else 0.0
        )

        if whitespace_count:
            confidence = whitespace_count / max(1, raw_profile["row_count"]) * 100
            _add_action(
                actions, column, "strip_whitespace", confidence,
                f"Detected leading or trailing whitespace in {whitespace_count} value(s).",
            )
        if profile.get("is_likely_id"):
            _add_action(
                actions, column, "preserve_identifier", unique_ratio * 100,
                f"The column has {profile.get('unique_count', 0)} unique values across {raw_profile['row_count']} rows and is likely an identifier; preserve it as an identifier.",
            )
        elif numeric_score >= 80 and is_string_like:
            _add_action(
                actions, column, "convert_to_numeric", numeric_score,
                f"{numeric_score:.1f}% of non-null values match a numeric pattern while the raw dtype is string-like.",
                {"numeric_like_percentage": numeric_score},
            )
        if datetime_score >= 80 and is_string_like:
            _add_action(
                actions, column, "convert_to_datetime", datetime_score,
                f"{datetime_score:.1f}% of non-null values parse as datetimes while the raw dtype is string-like.",
                {"datetime_like_percentage": datetime_score},
            )
        if boolean_score >= 80 and is_string_like:
            _add_action(
                actions, column, "convert_to_boolean", boolean_score,
                f"{boolean_score:.1f}% of non-null values match boolean representations such as yes/no or true/false.",
                {"boolean_like_percentage": boolean_score},
            )
        if profile.get("is_categorical"):
            _add_action(
                actions, column, "classify_as_categorical", (1.0 - unique_ratio) * 100,
                f"Only {profile.get('unique_count', 0)} unique values occur across {raw_profile['row_count']} rows, indicating low cardinality.",
            )
        if profile.get("is_free_text"):
            _add_action(
                actions, column, "preserve_free_text", unique_ratio * 100,
                "The column has high cardinality and variable-length string values, so it is likely free text.",
            )

    return PreprocessingPlan(
        actions=actions,
        reasoning="Actions were derived from the preserved raw profile evidence; no data was modified.",
        source="raw_profile_rule_engine",
    )


# Short alias for callers that already use the project naming convention.
generate_preprocessing_plan = generate_preprocessing_plan_from_raw_profile

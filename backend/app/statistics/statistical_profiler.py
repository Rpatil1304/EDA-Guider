"""Statistical profiling for the internally cleaned dataset.

This module calculates deterministic, local statistical evidence from the
cleaned DataFrame produced by the preprocessing stage.

It does not:
- modify the input DataFrame,
- perform preprocessing,
- make semantic-type decisions,
- analyze excluded columns,
- use an LLM,
- expose raw sample values.

The profiler respects the downstream_handoff produced by the preprocessing
summary and uses the cleaned profile to determine each column's semantic type.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.schemas.statistics import (
    BooleanStatistics,
    CategoricalStatistics,
    ColumnStatistics,
    DatetimeStatistics,
    NumericStatistics,
    StatisticalProfile,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Keep categorical evidence bounded.
# We do not want a high-cardinality column to create a huge evidence object.
_TOP_CATEGORY_LIMIT = 10


# ---------------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------------


def _safe_float(value: Any) -> float | None:
    """Return a finite Python float, otherwise None."""

    try:
        value = float(value)
    except (TypeError, ValueError):
        return None

    if not np.isfinite(value):
        return None

    return value


def _percentage(part: int, total: int) -> float:
    """Safely calculate a percentage."""

    if total <= 0:
        return 0.0

    return (part / total) * 100.0


def _get_column_profiles(
    preprocessing_summary: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Create a name -> cleaned-profile mapping."""

    cleaned_profile = preprocessing_summary.get(
        "cleaned_profile",
        {},
    )

    columns = cleaned_profile.get("columns", [])

    if not isinstance(columns, list):
        return {}

    result: dict[str, dict[str, Any]] = {}

    for column in columns:
        if not isinstance(column, dict):
            continue

        name = column.get("name")

        if name is None:
            continue

        result[str(name)] = column

    return result


def _get_eligible_columns(
    df: pd.DataFrame,
    preprocessing_summary: dict[str, Any],
) -> list[str]:
    """Return columns explicitly allowed by the downstream handoff."""

    handoff = preprocessing_summary.get(
        "downstream_handoff",
        {},
    )

    if not isinstance(handoff, dict):
        return []

    eligible_columns = handoff.get(
        "eligible_columns",
        [],
    )

    if not isinstance(eligible_columns, list):
        return []

    # Only keep columns that actually exist in the DataFrame.
    return [
        column
        for column in eligible_columns
        if column in df.columns
    ]


# ---------------------------------------------------------------------------
# Numeric statistics
# ---------------------------------------------------------------------------


def _calculate_numeric_statistics(
    series: pd.Series,
) -> NumericStatistics:
    """Calculate deterministic statistics for a numeric column."""

    numeric_series = pd.to_numeric(
        series,
        errors="coerce",
    )

    valid = numeric_series.dropna()

    count = int(valid.shape[0])

    if count == 0:
        return NumericStatistics()

    mean = _safe_float(valid.mean())
    median = _safe_float(valid.median())
    std = _safe_float(valid.std())

    minimum = _safe_float(valid.min())
    maximum = _safe_float(valid.max())

    q1 = _safe_float(valid.quantile(0.25))
    q3 = _safe_float(valid.quantile(0.75))

    skewness = _safe_float(valid.skew())
    kurtosis = _safe_float(valid.kurtosis())

    iqr = None
    lower_bound = None
    upper_bound = None
    outlier_count = 0

    if q1 is not None and q3 is not None:

        iqr = q3 - q1

        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        outliers = valid[
            (valid < lower_bound)
            | (valid > upper_bound)
        ]

        outlier_count = int(outliers.shape[0])

    return NumericStatistics(
        count=count,
        mean=mean,
        median=median,
        std=std,
        minimum=minimum,
        maximum=maximum,
        q1=q1,
        q3=q3,
        skewness=skewness,
        kurtosis=kurtosis,
        iqr=_safe_float(iqr),
        lower_bound=_safe_float(lower_bound),
        upper_bound=_safe_float(upper_bound),
        outlier_count=outlier_count,
        outlier_percentage=_percentage(
            outlier_count,
            count,
        ),
    )


# ---------------------------------------------------------------------------
# Categorical statistics
# ---------------------------------------------------------------------------


def _calculate_categorical_statistics(
    series: pd.Series,
) -> CategoricalStatistics:
    """Calculate frequency-based statistics for a categorical column."""

    valid = series.dropna()

    count = int(valid.shape[0])

    unique_count = int(
        valid.nunique(dropna=True)
    )

    if count == 0:
        return CategoricalStatistics(
            count=0,
            unique_count=0,
        )

    frequencies = valid.value_counts(
        dropna=True,
    )

    if frequencies.empty:
        return CategoricalStatistics(
            count=count,
            unique_count=unique_count,
        )

    top_value = frequencies.index[0]
    top_frequency = int(frequencies.iloc[0])

    top_categories_series = frequencies.head(
        _TOP_CATEGORY_LIMIT
    )

    top_categories = {
        str(category): int(frequency)
        for category, frequency
        in top_categories_series.items()
    }

    return CategoricalStatistics(
        count=count,
        unique_count=unique_count,
        top=str(top_value),
        top_frequency=top_frequency,
        top_percentage=_percentage(
            top_frequency,
            count,
        ),
        top_categories=top_categories,
    )


# ---------------------------------------------------------------------------
# Datetime statistics
# ---------------------------------------------------------------------------


def _calculate_datetime_statistics(
    series: pd.Series,
) -> DatetimeStatistics:
    """Calculate statistics for a datetime column."""

    datetime_series = pd.to_datetime(
        series,
        errors="coerce",
    )

    valid = datetime_series.dropna()

    count = int(valid.shape[0])

    unique_count = int(
        valid.nunique()
    )

    if count == 0:
        return DatetimeStatistics(
            count=0,
            unique_count=0,
        )

    minimum = valid.min()
    maximum = valid.max()

    duration_days = (
        maximum - minimum
    ).total_seconds() / (24 * 60 * 60)

    return DatetimeStatistics(
        count=count,
        minimum=minimum.isoformat(),
        maximum=maximum.isoformat(),
        unique_count=unique_count,
        duration_days=_safe_float(
            duration_days
        ),
    )


# ---------------------------------------------------------------------------
# Boolean statistics
# ---------------------------------------------------------------------------


def _calculate_boolean_statistics(
    series: pd.Series,
) -> BooleanStatistics:
    """Calculate statistics for a boolean column."""

    valid = series.dropna()

    count = int(valid.shape[0])

    if count == 0:
        return BooleanStatistics()

    # Normally preprocessing will already have converted the column to
    # boolean. This normalization also keeps the profiler robust when
    # receiving boolean-like values.
    normalized = (
        valid.astype(str)
        .str.strip()
        .str.lower()
    )

    true_count = int(
        normalized.isin(
            {"true", "yes", "y", "1"}
        ).sum()
    )

    false_count = int(
        normalized.isin(
            {"false", "no", "n", "0"}
        ).sum()
    )

    return BooleanStatistics(
        count=count,
        true_count=true_count,
        false_count=false_count,
        true_percentage=_percentage(
            true_count,
            count,
        ),
        false_percentage=_percentage(
            false_count,
            count,
        ),
    )


# ---------------------------------------------------------------------------
# Correlation
# ---------------------------------------------------------------------------


def _calculate_correlation_matrix(
    df: pd.DataFrame,
    numeric_columns: list[str],
) -> dict[str, dict[str, float]]:
    """Calculate Pearson correlation for eligible numeric columns."""

    if len(numeric_columns) < 2:
        return {}

    numeric_df = df[numeric_columns].apply(
        pd.to_numeric,
        errors="coerce",
    )

    correlation = numeric_df.corr(
        method="pearson",
    )

    result: dict[str, dict[str, float]] = {}

    for column in correlation.columns:

        result[column] = {}

        for other_column in correlation.columns:

            value = correlation.loc[
                column,
                other_column,
            ]

            safe_value = _safe_float(value)

            if safe_value is not None:
                result[column][other_column] = safe_value

    return result


# ---------------------------------------------------------------------------
# Main statistical profiler
# ---------------------------------------------------------------------------


def build_statistical_profile(
    df: pd.DataFrame,
    preprocessing_summary: dict[str, Any],
) -> StatisticalProfile:
    """Build a statistical profile from the cleaned DataFrame.

    Parameters
    ----------
    df:
        Internally cleaned DataFrame produced by preprocessing.

    preprocessing_summary:
        Part 6 preprocessing summary containing:
        - cleaned_profile
        - downstream_handoff
        - excluded_columns
        - unresolved_columns
        - needs_review_columns

    Returns
    -------
    StatisticalProfile
        Structured statistical evidence for downstream EDA stages.

    Notes
    -----
    The DataFrame is treated as read-only. No values are modified.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "df must be a pandas DataFrame."
        )

    if not isinstance(
        preprocessing_summary,
        dict,
    ):
        raise TypeError(
            "preprocessing_summary must be a dictionary."
        )

    n_rows = int(df.shape[0])
    n_cols = int(df.shape[1])

    profile = StatisticalProfile(
        n_rows=n_rows,
        n_cols=n_cols,
    )

    # ---------------------------------------------------------------
    # Obtain semantic information from the existing cleaned profile.
    # ---------------------------------------------------------------

    column_profiles = _get_column_profiles(
        preprocessing_summary
    )

    # ---------------------------------------------------------------
    # Respect the existing downstream handoff.
    #
    # The profiler does NOT decide eligibility itself.
    # ---------------------------------------------------------------

    eligible_columns = _get_eligible_columns(
        df,
        preprocessing_summary,
    )

    eligible_numeric_columns: list[str] = []

    # ---------------------------------------------------------------
    # Process each eligible column.
    # ---------------------------------------------------------------

    for column in eligible_columns:

        series = df[column]

        column_profile = column_profiles.get(
            str(column),
            {},
        )

        inferred_type = str(
            column_profile.get(
                "semantic_type",
                "unresolved",
            )
        )

        # -----------------------------------------------------------
        # General statistics
        # -----------------------------------------------------------

        missing_count = int(
            series.isna().sum()
        )

        count = n_rows - missing_count

        unique_count = int(
            series.nunique(
                dropna=True
            )
        )

        missing_percentage = _percentage(
            missing_count,
            n_rows,
        )

        unique_percentage = _percentage(
            unique_count,
            count,
        )

        numeric_statistics = None
        categorical_statistics = None
        datetime_statistics = None
        boolean_statistics = None

        # -----------------------------------------------------------
        # Numeric
        # -----------------------------------------------------------

        if inferred_type == "numeric":

            numeric_statistics = (
                _calculate_numeric_statistics(
                    series
                )
            )

            profile.numeric_columns[
                column
            ] = numeric_statistics

            eligible_numeric_columns.append(
                column
            )

        # -----------------------------------------------------------
        # Categorical
        # -----------------------------------------------------------

        elif inferred_type == "categorical":

            categorical_statistics = (
                _calculate_categorical_statistics(
                    series
                )
            )

            profile.categorical_columns[
                column
            ] = categorical_statistics

        # -----------------------------------------------------------
        # Datetime
        # -----------------------------------------------------------

        elif inferred_type == "datetime":

            datetime_statistics = (
                _calculate_datetime_statistics(
                    series
                )
            )

            profile.datetime_columns[
                column
            ] = datetime_statistics

        # -----------------------------------------------------------
        # Boolean
        # -----------------------------------------------------------

        elif inferred_type == "boolean":

            boolean_statistics = (
                _calculate_boolean_statistics(
                    series
                )
            )

            profile.boolean_columns[
                column
            ] = boolean_statistics

        # -----------------------------------------------------------
        # General column-level profile
        # -----------------------------------------------------------

        profile.columns[
            column
        ] = ColumnStatistics(
            name=column,
            inferred_type=inferred_type,
            count=count,
            missing_count=missing_count,
            missing_percentage=missing_percentage,
            unique_count=unique_count,
            unique_percentage=unique_percentage,
            numeric=numeric_statistics,
            categorical=categorical_statistics,
            datetime=datetime_statistics,
            boolean=boolean_statistics,
        )

    # ---------------------------------------------------------------
    # Correlation matrix
    # ---------------------------------------------------------------

    profile.correlation_matrix = (
        _calculate_correlation_matrix(
            df,
            eligible_numeric_columns,
        )
    )

    return profile
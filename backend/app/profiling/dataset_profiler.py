# dataset_profiler.py
#
# This file creates the overall profile
# of the complete dataset.
#
# Flow:
#
# DataFrame
#     ↓
# profile_column()
#     ↓
# ColumnProfile for every column
#     ↓
# Dataset-level statistics
#     ↓
# DatasetProfile


import pandas as pd

from app.profiling.column_profiler import (
    profile_column
)

from app.profiling.quality import (
    get_duplicate_row_info
)

from app.schemas.profile import (
    ColumnProfile,
    DatasetProfile
)


# ============================================================
# 1. DATASET QUALITY SUMMARY
# ============================================================

def get_dataset_quality_summary(
    column_profiles: list[ColumnProfile]
) -> dict:
    """
    Create a high-level quality summary
    from all column profiles.

    This function does not modify the data.
    """

    total_columns = len(
        column_profiles
    )

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    columns_with_missing = sum(
        profile.missing_count > 0
        for profile in column_profiles
    )

    # --------------------------------------------------------
    # Null-like values
    # --------------------------------------------------------

    columns_with_null_like_values = sum(
        profile.null_like_count > 0
        for profile in column_profiles
    )

    # --------------------------------------------------------
    # Whitespace
    # --------------------------------------------------------

    columns_with_whitespace = sum(
        profile.has_whitespace
        for profile in column_profiles
    )

    # --------------------------------------------------------
    # Empty strings
    # --------------------------------------------------------

    columns_with_empty_strings = sum(
        profile.has_empty_strings
        for profile in column_profiles
    )

    # --------------------------------------------------------
    # Mixed data types
    # --------------------------------------------------------

    columns_with_mixed_types = sum(
        profile.has_mixed_types
        for profile in column_profiles
    )

    # --------------------------------------------------------
    # Case variations
    # --------------------------------------------------------

    columns_with_case_variations = sum(
        profile.has_case_variations
        for profile in column_profiles
    )

    # --------------------------------------------------------
    # Constant columns
    # --------------------------------------------------------

    constant_columns = sum(
        profile.is_constant
        for profile in column_profiles
    )

    # --------------------------------------------------------
    # Potential ID columns
    # --------------------------------------------------------

    potential_id_columns = sum(
        profile.is_potential_id
        for profile in column_profiles
    )

    # --------------------------------------------------------
    # Columns containing outliers
    # --------------------------------------------------------

    columns_with_outliers = sum(
        profile.outlier_count > 0
        for profile in column_profiles
    )

    # --------------------------------------------------------
    # Columns containing invalid values
    # --------------------------------------------------------

    columns_with_invalid_values = sum(
        profile.invalid_parse_count > 0
        for profile in column_profiles
    )

    return {

        "total_columns":
            total_columns,

        "columns_with_missing":
            columns_with_missing,

        "columns_with_null_like_values":
            columns_with_null_like_values,

        "columns_with_whitespace":
            columns_with_whitespace,

        "columns_with_empty_strings":
            columns_with_empty_strings,

        "columns_with_mixed_types":
            columns_with_mixed_types,

        "columns_with_case_variations":
            columns_with_case_variations,

        "constant_columns":
            constant_columns,

        "potential_id_columns":
            potential_id_columns,

        "columns_with_outliers":
            columns_with_outliers,

        "columns_with_invalid_values":
            columns_with_invalid_values,
    }


# ============================================================
# 2. COMPLETE DATASET PROFILE
# ============================================================

def profile_dataset(
    df: pd.DataFrame
) -> DatasetProfile:
    """
    Create a complete DatasetProfile.

    Every column is analyzed using profile_column().

    Dataset-level duplicate rows are also calculated.

    The original DataFrame is never modified.
    """

    # --------------------------------------------------------
    # Profile every column
    # --------------------------------------------------------

    column_profiles = []

    for column in df.columns:

        profile = profile_column(
            df[column]
        )

        column_profiles.append(
            profile
        )

    # --------------------------------------------------------
    # Dataset-level duplicate rows
    # --------------------------------------------------------

    (
        duplicate_row_count,
        duplicate_row_percentage
    ) = get_duplicate_row_info(df)

    # --------------------------------------------------------
    # Dataset-level quality summary
    # --------------------------------------------------------

    quality_summary = (
        get_dataset_quality_summary(
            column_profiles
        )
    )

    # --------------------------------------------------------
    # Create final DatasetProfile
    # --------------------------------------------------------

    return DatasetProfile(

        row_count=len(df),

        column_count=len(df.columns),

        duplicate_row_count=(
            duplicate_row_count
        ),

        duplicate_row_percentage=(
            duplicate_row_percentage
        ),

        column_profiles=(
            column_profiles
        ),

        quality_summary=(
            quality_summary
        ),
    )
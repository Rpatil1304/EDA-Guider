# column_profiler.py will bring all profiling results
# together for each column.


import pandas as pd

from data_structures.profile import ColumnProfile

from profiling.type_inference import (
    infer_semantic_type,
    get_numeric_parseable_percentage,
    get_datetime_parseable_percentage,
    get_boolean_parseable_percentage,
    has_case_variations,
    has_mixed_types,
    is_constant,
    is_potential_id,
    infer_categorical_or_text,
)

from profiling.quality import (
    get_missing_value_info,
    get_unique_value_info,
    has_duplicate_values,
    get_whitespace_info,
    get_empty_string_info,
    get_outlier_info,
    get_null_like_count,
)


def get_basic_column_profile(
    series: pd.Series
) -> dict:
    """
    Collect basic type-related information
    for a single column.

    This function does not modify the original data.
    """

    return {
        "name": series.name,
        "raw_dtype": str(series.dtype),

        "inferred_type":
            infer_semantic_type(series),

        "numeric_parseable_percentage":
            get_numeric_parseable_percentage(series),

        "datetime_parseable_percentage":
            get_datetime_parseable_percentage(series),

        "boolean_parseable_percentage":
            get_boolean_parseable_percentage(series),
    }


def get_column_quality_profile(
    series: pd.Series
) -> dict:
    """
    Collect data-quality information
    for a single column.

    This function only analyzes the data.
    It does not modify the original Series.
    """

    missing_count, missing_percentage = (
        get_missing_value_info(series)
    )

    unique_count, unique_percentage = (
        get_unique_value_info(series)
    )

    whitespace_count, whitespace_percentage = (
        get_whitespace_info(series)
    )

    empty_string_count, empty_string_percentage = (
        get_empty_string_info(series)
    )

    outlier_count, outlier_percentage = (
        get_outlier_info(series)
    )

    null_like_count = get_null_like_count(series)

    return {
        "missing_count": missing_count,
        "missing_percentage": missing_percentage,

        "unique_count": unique_count,
        "unique_percentage": unique_percentage,

        "has_duplicate_values":
            has_duplicate_values(series),

        "whitespace_count": whitespace_count,
        "whitespace_percentage": whitespace_percentage,

        "empty_string_count": empty_string_count,
        "empty_string_percentage": empty_string_percentage,

        "null_like_count": null_like_count,

        "outlier_count": outlier_count,
        "outlier_percentage": outlier_percentage,
    }


def get_special_characteristics(
    series: pd.Series
) -> dict:
    """
    Collect special characteristics of a column.

    These are observations used later by the
    preprocessing and rule-engine stages.

    The original data is not modified.
    """

    semantic_type = infer_categorical_or_text(series)

    return {
        "has_case_variations":
            has_case_variations(series),

        "has_mixed_types":
            has_mixed_types(series),

        "is_constant":
            is_constant(series),

        "is_potential_id":
            is_potential_id(series),

        "is_potential_text":
            semantic_type == "text",
    }


def profile_column(
    series: pd.Series
) -> ColumnProfile:
    """
    Create a complete ColumnProfile for a single column.

    This function combines:

        - basic type information
        - type-conversion information
        - quality information
        - special characteristics
        - preprocessing observations

    The original data is never modified.
    """

    basic_profile = (
        get_basic_column_profile(series)
    )

    quality_profile = (
        get_column_quality_profile(series)
    )

    special_characteristics = (
        get_special_characteristics(series)
    )

    preprocessing_flags = []

    # --------------------------------------------------------
    # Generate observations for later preprocessing.
    #
    # These flags DO NOT perform preprocessing.
    # They only record what was detected.
    # --------------------------------------------------------

    if quality_profile["missing_percentage"] > 0:
        preprocessing_flags.append(
            "missing_values_present"
        )

    if quality_profile["null_like_count"] > 0:
        preprocessing_flags.append(
            "null_like_values_present"
        )

    if quality_profile["whitespace_count"] > 0:
        preprocessing_flags.append(
            "leading_or_trailing_whitespace"
        )

    if quality_profile["empty_string_count"] > 0:
        preprocessing_flags.append(
            "empty_strings_present"
        )

    if special_characteristics[
        "has_case_variations"
    ]:
        preprocessing_flags.append(
            "case_variations_present"
        )

    if special_characteristics[
        "has_mixed_types"
    ]:
        preprocessing_flags.append(
            "mixed_types_present"
        )

    if special_characteristics[
        "is_constant"
    ]:
        preprocessing_flags.append(
            "constant_column"
        )

    if special_characteristics[
        "is_potential_id"
    ]:
        preprocessing_flags.append(
            "potential_id_column"
        )

    if quality_profile["outlier_count"] > 0:
        preprocessing_flags.append(
            "statistical_outliers_present"
        )

    # --------------------------------------------------------
    # Create final ColumnProfile
    # --------------------------------------------------------

    return ColumnProfile(

        # ----------------------------------------------------
        # Basic column information
        # ----------------------------------------------------

        name=basic_profile["name"],

        raw_dtype=basic_profile["raw_dtype"],

        inferred_type=basic_profile[
            "inferred_type"
        ],

        row_count=len(series),

        # ----------------------------------------------------
        # Missing-value information
        # ----------------------------------------------------

        missing_count=quality_profile[
            "missing_count"
        ],

        missing_percentage=quality_profile[
            "missing_percentage"
        ],

        null_like_count=quality_profile[
            "null_like_count"
        ],

        # ----------------------------------------------------
        # Cardinality / uniqueness
        # ----------------------------------------------------

        unique_count=quality_profile[
            "unique_count"
        ],

        unique_percentage=quality_profile[
            "unique_percentage"
        ],

        # ----------------------------------------------------
        # Data-quality observations
        # ----------------------------------------------------

        has_whitespace=(
            quality_profile[
                "whitespace_count"
            ] > 0
        ),

        whitespace_count=quality_profile[
            "whitespace_count"
        ],

        whitespace_percentage=quality_profile[
            "whitespace_percentage"
        ],

        has_empty_strings=(
            quality_profile[
                "empty_string_count"
            ] > 0
        ),

        empty_string_count=quality_profile[
            "empty_string_count"
        ],

        empty_string_percentage=quality_profile[
            "empty_string_percentage"
        ],

        # ----------------------------------------------------
        # Type-conversion / semantic information
        # ----------------------------------------------------

        numeric_parseable_percentage=basic_profile[
            "numeric_parseable_percentage"
        ],

        datetime_parseable_percentage=basic_profile[
            "datetime_parseable_percentage"
        ],

        boolean_parseable_percentage=basic_profile[
            "boolean_parseable_percentage"
        ],

        # ----------------------------------------------------
        # Special characteristics
        # ----------------------------------------------------

        has_case_variations=special_characteristics[
            "has_case_variations"
        ],

        has_mixed_types=special_characteristics[
            "has_mixed_types"
        ],

        is_constant=special_characteristics[
            "is_constant"
        ],

        is_potential_id=special_characteristics[
            "is_potential_id"
        ],

        is_potential_text=special_characteristics[
            "is_potential_text"
        ],

        # ----------------------------------------------------
        # Statistical observations
        # ----------------------------------------------------

        outlier_count=quality_profile[
            "outlier_count"
        ],

        outlier_percentage=quality_profile[
            "outlier_percentage"
        ],

        # ----------------------------------------------------
        # Raw-value examples
        # ----------------------------------------------------

        sample_values=(
            series.dropna()
            .head(5)
            .tolist()
        ),

        # ----------------------------------------------------
        # Preprocessing observations
        # ----------------------------------------------------

        preprocessing_flags=preprocessing_flags,
    )
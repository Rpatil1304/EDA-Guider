# column_profiler.py
#
# This file brings all profiling results together
# for a single column.
#
# IMPORTANT:
# - This module only analyzes data.
# - It never modifies the original Series.
# - It combines type inference + quality analysis
#   into a ColumnProfile object.


import pandas as pd

from app.schemas.profile import ColumnProfile

from app.profiling.type_inference import (
    infer_semantic_type,
    get_numeric_parseable_percentage,
    get_datetime_parseable_percentage,
    get_boolean_parseable_percentage,
    get_percentage_parseable_percentage,
    get_currency_parseable_percentage,
    has_case_variations,
    has_mixed_types,
    is_constant,
    is_potential_id,
    infer_categorical_or_text,
)

from app.profiling.quality import (
    get_missing_value_info,
    get_unique_value_info,
    has_duplicate_values,
    get_whitespace_info,
    get_empty_string_info,
    get_outlier_info,
    get_null_like_count,
)


# ============================================================
# 1. BASIC COLUMN PROFILE
# ============================================================

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

        "raw_dtype":
            str(series.dtype),

        "inferred_type":
            infer_semantic_type(series),

        "numeric_parseable_percentage":
            get_numeric_parseable_percentage(series),

        "datetime_parseable_percentage":
            get_datetime_parseable_percentage(series),

        "boolean_parseable_percentage":
            get_boolean_parseable_percentage(series),

        "percentage_parseable_percentage":
            get_percentage_parseable_percentage(series),

        "currency_parseable_percentage":
            get_currency_parseable_percentage(series),
    }


# ============================================================
# 2. QUALITY PROFILE
# ============================================================

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

    null_like_count = (
        get_null_like_count(series)
    )

    return {

        # ----------------------------------------------------
        # Missing values
        # ----------------------------------------------------

        "missing_count":
            missing_count,

        "missing_percentage":
            missing_percentage,

        "null_like_count":
            null_like_count,

        # ----------------------------------------------------
        # Cardinality
        # ----------------------------------------------------

        "unique_count":
            unique_count,

        "unique_percentage":
            unique_percentage,

        "has_duplicate_values":
            has_duplicate_values(series),

        # ----------------------------------------------------
        # Whitespace
        # ----------------------------------------------------

        "whitespace_count":
            whitespace_count,

        "whitespace_percentage":
            whitespace_percentage,

        # ----------------------------------------------------
        # Empty strings
        # ----------------------------------------------------

        "empty_string_count":
            empty_string_count,

        "empty_string_percentage":
            empty_string_percentage,

        # ----------------------------------------------------
        # Statistical observations
        # ----------------------------------------------------

        "outlier_count":
            outlier_count,

        "outlier_percentage":
            outlier_percentage,
    }


# ============================================================
# 3. SPECIAL CHARACTERISTICS
# ============================================================

def get_special_characteristics(
    series: pd.Series
) -> dict:
    """
    Collect special characteristics of a column.

    These are observations used later by the
    preprocessing and rule-engine stages.

    The original data is not modified.
    """

    semantic_type = (
        infer_categorical_or_text(series)
    )

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


# ============================================================
# 4. INVALID PARSE COUNT
# ============================================================

def get_invalid_parse_count(
    series: pd.Series,
    inferred_type: str
) -> int:
    """
    Determine how many semantic non-null values could not
    be parsed according to the inferred semantic type.

    This is an observation only.

    It does not modify the data.
    """

    # --------------------------------------------------------
    # Values that are genuinely missing or textual
    # representations of missing values are excluded.
    # --------------------------------------------------------

    null_like_values = {
        "",
        "na",
        "n/a",
        "nan",
        "null",
        "none",
        "missing",
    }

    normalized = series.copy()

    if (
        pd.api.types.is_object_dtype(normalized)
        or pd.api.types.is_string_dtype(normalized)
    ):
        normalized = normalized.map(
            lambda value:
            value.strip()
            if isinstance(value, str)
            else value
        )

    def is_null_like(value) -> bool:

        if pd.isna(value):
            return True

        if isinstance(value, str):
            return (
                value.lower()
                in null_like_values
            )

        return False

    semantic_values = normalized[
        ~normalized.map(is_null_like)
    ]

    if semantic_values.empty:
        return 0

    # --------------------------------------------------------
    # Numeric
    # --------------------------------------------------------

    if inferred_type in (
        "integer",
        "float",
    ):

        parsed = pd.to_numeric(
            semantic_values,
            errors="coerce"
        )

        return int(
            parsed.isna().sum()
        )

    # --------------------------------------------------------
    # Datetime
    # --------------------------------------------------------

    if inferred_type == "datetime":

        parsed = pd.to_datetime(
            semantic_values,
            errors="coerce",
            format="mixed"
        )

        return int(
            parsed.isna().sum()
        )

    # --------------------------------------------------------
    # Boolean
    # --------------------------------------------------------

    if inferred_type == "boolean":

        valid_boolean_values = {
            "true",
            "false",
            "yes",
            "no",
            "y",
            "n",
            "1",
            "0",
        }

        def is_boolean_like(value) -> bool:

            if isinstance(value, bool):
                return True

            if isinstance(value, str):
                return (
                    value.lower()
                    in valid_boolean_values
                )

            if isinstance(value, int):
                return value in (0, 1)

            return False

        valid_mask = semantic_values.map(
            is_boolean_like
        )

        return int(
            (~valid_mask).sum()
        )

    # --------------------------------------------------------
    # Percentage
    # --------------------------------------------------------

    if inferred_type == "percentage":

        def is_percentage(value) -> bool:

            if not isinstance(value, str):
                return False

            value = value.strip()

            if not value.endswith("%"):
                return False

            numeric_part = (
                value[:-1]
                .strip()
            )

            try:
                float(numeric_part)
                return True
            except ValueError:
                return False

        valid_mask = semantic_values.map(
            is_percentage
        )

        return int(
            (~valid_mask).sum()
        )

    # --------------------------------------------------------
    # Currency
    # --------------------------------------------------------

    if inferred_type == "currency":

        currency_symbols = {
            "$",
            "€",
            "£",
            "₹",
        }

        def is_currency(value) -> bool:

            if not isinstance(value, str):
                return False

            value = value.strip()

            if not value:
                return False

            if value[0] not in currency_symbols:
                return False

            numeric_part = (
                value[1:]
                .strip()
                .replace(",", "")
            )

            try:
                float(numeric_part)
                return True
            except ValueError:
                return False

        valid_mask = semantic_values.map(
            is_currency
        )

        return int(
            (~valid_mask).sum()
        )

    # --------------------------------------------------------
    # Categorical / text / other types
    # --------------------------------------------------------

    return 0


# ============================================================
# 5. COMPLETE COLUMN PROFILE
# ============================================================

def profile_column(
    series: pd.Series
) -> ColumnProfile:
    """
    Create a complete ColumnProfile for one column.

    Combines:

        - basic type information
        - semantic type information
        - quality information
        - special characteristics
        - preprocessing observations

    The original data is never modified.
    """

    # --------------------------------------------------------
    # Collect profiling information
    # --------------------------------------------------------

    basic_profile = (
        get_basic_column_profile(series)
    )

    quality_profile = (
        get_column_quality_profile(series)
    )

    special_characteristics = (
        get_special_characteristics(series)
    )

    inferred_type = (
        basic_profile["inferred_type"]
    )

    # --------------------------------------------------------
    # Invalid values
    # --------------------------------------------------------

    invalid_parse_count = (
        get_invalid_parse_count(
            series,
            inferred_type
        )
    )

    # --------------------------------------------------------
    # Preprocessing flags
    #
    # These flags ONLY describe observations.
    # They do not modify the data.
    # --------------------------------------------------------

    preprocessing_flags = []

    if quality_profile[
        "missing_count"
    ] > 0:

        preprocessing_flags.append(
            "missing_values_present"
        )

    if quality_profile[
        "null_like_count"
    ] > 0:

        preprocessing_flags.append(
            "null_like_values_present"
        )

    if quality_profile[
        "whitespace_count"
    ] > 0:

        preprocessing_flags.append(
            "leading_or_trailing_whitespace"
        )

    if quality_profile[
        "empty_string_count"
    ] > 0:

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

    if invalid_parse_count > 0:

        preprocessing_flags.append(
            "invalid_values_present"
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

    if quality_profile[
        "outlier_count"
    ] > 0:

        preprocessing_flags.append(
            "statistical_outliers_present"
        )

    # --------------------------------------------------------
    # Sample values
    # --------------------------------------------------------

    sample_values = (
        series
        .dropna()
        .head(5)
        .tolist()
    )

    # --------------------------------------------------------
    # Create ColumnProfile
    # --------------------------------------------------------

    return ColumnProfile(

        # ----------------------------------------------------
        # Basic information
        # ----------------------------------------------------

        name=basic_profile[
            "name"
        ],

        raw_dtype=basic_profile[
            "raw_dtype"
        ],

        inferred_type=inferred_type,

        row_count=len(series),

        # ----------------------------------------------------
        # Missing values
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
        # Cardinality
        # ----------------------------------------------------

        unique_count=quality_profile[
            "unique_count"
        ],

        unique_percentage=quality_profile[
            "unique_percentage"
        ],

        # ----------------------------------------------------
        # Whitespace
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

        # ----------------------------------------------------
        # Empty strings
        # ----------------------------------------------------

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
        # Invalid parsing
        # ----------------------------------------------------

        invalid_parse_count=(
            invalid_parse_count
        ),

        # ----------------------------------------------------
        # Parseability
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
        # Raw samples
        # ----------------------------------------------------

        sample_values=sample_values,

        # ----------------------------------------------------
        # Preprocessing observations
        # ----------------------------------------------------

        preprocessing_flags=preprocessing_flags,
    )
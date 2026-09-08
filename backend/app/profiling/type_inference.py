# type_inference.py
#
# This module analyzes the semantic type of a column.
#
# IMPORTANT:
# - This module ONLY analyzes data.
# - It never modifies the original DataFrame/Series.
# - Raw representation and semantic meaning are treated separately.


import re

import pandas as pd


# ============================================================
# CONSTANTS
# ============================================================

NULL_LIKE_VALUES = {
    "",
    "na",
    "n/a",
    "nan",
    "null",
    "none",
    "missing",
}

BOOLEAN_VALUES = {
    "true",
    "false",
    "yes",
    "no",
    "y",
    "n",
}

PERCENTAGE_PATTERN = re.compile(
    r"^[+-]?\d+(\.\d+)?\s*%$"
)

CURRENCY_PATTERN = re.compile(
    r"^[\s]*"
    r"[\$€£₹]"
    r"\s*"
    r"[+-]?"
    r"\d[\d,]*(\.\d+)?"
    r"\s*$"
)


# ============================================================
# 1. BASIC PANDAS TYPE
# ============================================================

def infer_basic_type(
    series: pd.Series
) -> str:
    """
    Infer the basic datatype using Pandas dtype.

    This function is used only when Pandas can reliably
    identify the datatype.
    """

    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    if pd.api.types.is_integer_dtype(series):
        return "integer"

    if pd.api.types.is_float_dtype(series):
        return "float"

    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    if pd.api.types.is_timedelta64_dtype(series):
        return "timedelta"

    if pd.api.types.is_complex_dtype(series):
        return "complex"

    return "unknown"


# ============================================================
# 2. TEMPORARY NORMALIZATION
# ============================================================

def normalize_for_inference(
    series: pd.Series
) -> pd.Series:
    """
    Create a temporary normalized copy for inference.

    Only leading and trailing whitespace is removed.

    Case is preserved.

    The original Series is never modified.
    """

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

    return normalized


def _is_null_like(value) -> bool:
    """
    Determine whether a value represents missing data
    for semantic inference.
    """

    if pd.isna(value):
        return True

    if isinstance(value, str):
        return (
            value.strip().lower()
            in NULL_LIKE_VALUES
        )

    return False


def _get_semantic_non_null_values(
    series: pd.Series
) -> pd.Series:
    """
    Return values that are not actual or textual
    missing-value markers.

    This is only a temporary view for inference.
    """

    normalized = normalize_for_inference(series)

    return normalized[
        ~normalized.map(_is_null_like)
    ]


# ============================================================
# 3. NUMERIC ANALYSIS
# ============================================================

def get_numeric_parseable_percentage(
    series: pd.Series
) -> float:
    """
    Calculate the percentage of semantic non-null values
    that can directly be parsed as numeric.

    Symbols such as %, $, commas, etc. are NOT removed.
    """

    non_null = _get_semantic_non_null_values(series)

    if non_null.empty:
        return 0.0

    numeric_values = pd.to_numeric(
        non_null,
        errors="coerce"
    )

    return float(
        numeric_values.notna().mean() * 100
    )


def infer_numeric_string_type(
    series: pd.Series
) -> str:
    """
    Infer whether a column represents integer or float.

    Mixed representations are allowed.

    Example:

        25
        "30"
        " 35 "
        40

    is inferred as integer.
    """

    non_null = _get_semantic_non_null_values(series)

    if non_null.empty:
        return "unknown"

    numeric_values = pd.to_numeric(
        non_null,
        errors="coerce"
    )

    parseable_mask = numeric_values.notna()

    if not parseable_mask.any():
        return "unknown"

    parseable_percentage = (
        parseable_mask.mean() * 100
    )

    if parseable_percentage < 70:
        return "unknown"

    valid_numeric_values = numeric_values[
        parseable_mask
    ]

    if (
        valid_numeric_values % 1 == 0
    ).all():
        return "integer"

    return "float"


# ============================================================
# 4. DATETIME ANALYSIS
# ============================================================

def get_datetime_parseable_percentage(
    series: pd.Series
) -> float:
    """
    Calculate the percentage of semantic non-null values
    that can be interpreted as datetime.

    Numeric columns are deliberately excluded because
    Pandas can interpret ordinary numbers as timestamps.
    """

    # IMPORTANT:
    # Do not try to interpret ordinary numeric columns
    # as dates.
    if pd.api.types.is_numeric_dtype(series):
        return 0.0

    if pd.api.types.is_bool_dtype(series):
        return 0.0

    non_null = _get_semantic_non_null_values(series)

    if non_null.empty:
        return 0.0

    datetime_values = pd.to_datetime(
        non_null,
        errors="coerce",
        format="mixed"
    )

    return float(
        datetime_values.notna().mean() * 100
    )


# ============================================================
# 5. BOOLEAN ANALYSIS
# ============================================================

def get_boolean_parseable_percentage(
    series: pd.Series
) -> float:
    """
    Calculate the percentage of semantic non-null values
    that represent boolean-like values.

    Supported representations:

        True / False
        Yes / No
        Y / N
        1 / 0
    """

    non_null = _get_semantic_non_null_values(series)

    if non_null.empty:
        return 0.0

    def is_boolean_like(value) -> bool:

        if isinstance(value, bool):
            return True

        if isinstance(value, str):
            return (
                value.strip().lower()
                in BOOLEAN_VALUES
            )

        if isinstance(value, int):
            return value in (0, 1)

        return False

    boolean_mask = non_null.map(
        is_boolean_like
    )

    return float(
        boolean_mask.mean() * 100
    )


# ============================================================
# 6. PERCENTAGE DETECTION
# ============================================================

def get_percentage_parseable_percentage(
    series: pd.Series
) -> float:
    """
    Calculate the percentage of semantic non-null values
    that look like percentages.

    Examples:

        10%
        25.5%
        -5%

    No conversion is performed.
    """

    non_null = _get_semantic_non_null_values(series)

    if non_null.empty:
        return 0.0

    def is_percentage(value) -> bool:

        if not isinstance(value, str):
            return False

        return bool(
            PERCENTAGE_PATTERN.match(
                value.strip()
            )
        )

    percentage_mask = non_null.map(
        is_percentage
    )

    return float(
        percentage_mask.mean() * 100
    )


# ============================================================
# 7. CURRENCY DETECTION
# ============================================================

def get_currency_parseable_percentage(
    series: pd.Series
) -> float:
    """
    Calculate the percentage of semantic non-null values
    that look like currency values.

    Examples:

        $1,000
        €2500
        £500.50
        ₹10,000

    No conversion is performed.
    """

    non_null = _get_semantic_non_null_values(series)

    if non_null.empty:
        return 0.0

    def is_currency(value) -> bool:

        if not isinstance(value, str):
            return False

        return bool(
            CURRENCY_PATTERN.match(
                value.strip()
            )
        )

    currency_mask = non_null.map(
        is_currency
    )

    return float(
        currency_mask.mean() * 100
    )


# ============================================================
# 8. CASE VARIATION
# ============================================================

def has_case_variations(
    series: pd.Series
) -> bool:
    """
    Detect whether values differ only by letter casing.

    Example:

        Pune
        pune
        PUNE

    returns True.

    Case is NOT changed in the original data.
    """

    non_null = series.dropna()

    string_values = non_null[
        non_null.map(
            lambda value:
            isinstance(value, str)
        )
    ]

    if string_values.empty:
        return False

    normalized = string_values.map(
        lambda value:
        value.strip().lower()
    )

    return (
        normalized.nunique()
        < string_values.nunique()
    )


# ============================================================
# 9. MIXED TYPES
# ============================================================

def has_mixed_types(
    series: pd.Series
) -> bool:
    """
    Detect multiple Python-level types.

    Example:

        100
        "200"
        300

    returns True.

    This does NOT mean semantic type is unknown.
    """

    non_null = series.dropna()

    if non_null.empty:
        return False

    python_types = non_null.map(
        lambda value: type(value)
    )

    return python_types.nunique() > 1


# ============================================================
# 10. CONSTANT COLUMN
# ============================================================

def is_constant(
    series: pd.Series
) -> bool:
    """
    Determine whether all non-null values are identical.
    """

    non_null = series.dropna()

    if non_null.empty:
        return False

    return non_null.nunique() == 1


# ============================================================
# 11. POTENTIAL ID
# ============================================================

def is_potential_id(
    series: pd.Series
) -> bool:
    """
    Heuristically determine whether a column may be an ID.

    IMPORTANT:

    Uniqueness alone is NOT enough.

    Numeric analytical columns such as:

        Age
        Salary
        Experience

    should not become IDs merely because their values
    happen to be unique.

    Strong column-name signals are preferred.
    """

    non_null = series.dropna()

    if non_null.empty:
        return False

    if is_constant(series):
        return False

    column_name = str(
        series.name
    ).strip().lower()

    id_keywords = (
        "id",
        "identifier",
        "uuid",
        "guid",
        "customer_code",
        "employee_code",
        "product_code",
        "account_number",
        "reference_number",
    )

    # Strong semantic name signal.
    if any(
        keyword in column_name
        for keyword in id_keywords
    ):
        return True

    # Generic names such as "number" or "no"
    # are intentionally NOT enough.
    #
    # This prevents:
    #
    # Age → ID
    # Salary → ID
    # Experience → ID

    return False


# ============================================================
# 12. CATEGORICAL VS TEXT
# ============================================================

def infer_categorical_or_text(
    series: pd.Series
) -> str:
    """
    Distinguish categorical values from free-form text.
    """

    non_null = _get_semantic_non_null_values(series)

    if non_null.empty:
        return "unknown"

    if is_constant(series):
        return "categorical"

    string_values = non_null[
        non_null.map(
            lambda value:
            isinstance(value, str)
        )
    ]

    if string_values.empty:
        return "unknown"

    unique_ratio = (
        string_values.nunique()
        / len(string_values)
    )

    average_length = (
        string_values
        .map(len)
        .mean()
    )

    # Long, highly unique strings are likely free-form text.
    if (
        unique_ratio >= 0.70
        and average_length >= 30
    ):
        return "text"

    return "categorical"


# ============================================================
# 13. MAIN SEMANTIC TYPE INFERENCE
# ============================================================

def infer_semantic_type(
    series: pd.Series
) -> str:
    """
    Determine the semantic type represented by a column.

    Possible results:

        boolean
        integer
        float
        datetime
        timedelta
        complex
        percentage
        currency
        categorical
        text
        unknown
    """

    if series.dropna().empty:
        return "unknown"

    # --------------------------------------------------------
    # Reliable Pandas types
    # --------------------------------------------------------

    basic_type = infer_basic_type(series)

    if basic_type != "unknown":
        return basic_type

    # --------------------------------------------------------
    # Constant values
    # --------------------------------------------------------

    # Constant values are treated as categorical because
    # one repeated value is not enough evidence to determine
    # semantic meaning.
    if is_constant(series):
        return "categorical"

    # --------------------------------------------------------
    # Percentage
    # --------------------------------------------------------

    percentage_percentage = (
        get_percentage_parseable_percentage(
            series
        )
    )

    if percentage_percentage >= 70:
        return "percentage"

    # --------------------------------------------------------
    # Currency
    # --------------------------------------------------------

    currency_percentage = (
        get_currency_parseable_percentage(
            series
        )
    )

    if currency_percentage >= 70:
        return "currency"

    # --------------------------------------------------------
    # Boolean
    # --------------------------------------------------------

    boolean_percentage = (
        get_boolean_parseable_percentage(
            series
        )
    )

    if boolean_percentage >= 70:
        return "boolean"

    # --------------------------------------------------------
    # Numeric
    # --------------------------------------------------------

    numeric_percentage = (
        get_numeric_parseable_percentage(
            series
        )
    )

    if numeric_percentage >= 70:

        numeric_type = (
            infer_numeric_string_type(
                series
            )
        )

        if numeric_type != "unknown":
            return numeric_type

    # --------------------------------------------------------
    # Datetime
    # --------------------------------------------------------

    datetime_percentage = (
        get_datetime_parseable_percentage(
            series
        )
    )

    if datetime_percentage >= 70:
        return "datetime"

    # --------------------------------------------------------
    # Categorical / Text
    # --------------------------------------------------------

    return infer_categorical_or_text(series)
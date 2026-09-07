# This file determines the semantic type of every column.
# It only analyzes the data.
# It does NOT modify the original DataFrame.


import pandas as pd


# 1. BASIC TYPE INFERENCE

def infer_basic_type(series: pd.Series) -> str:
    """
    Infer the basic type of a Pandas Series
    using its existing Pandas dtype.

    This function handles types that Pandas can
    identify reliably without inspecting string content.
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

# 2. NORMALIZATION FOR INFERENCE

def normalize_for_inference(series: pd.Series) -> pd.Series:
    """
    Create a temporary normalized copy of a Series
    for type detection.

    Only leading and trailing whitespace is removed.

    Case is preserved.

    The original dataset is never modified.
    """

    normalized = series.copy()

    if (
        pd.api.types.is_object_dtype(normalized)
        or pd.api.types.is_string_dtype(normalized)
    ):
        normalized = normalized.map(
            lambda value: value.strip()
            if isinstance(value, str)
            else value
        )

    return normalized


# 3. NUMERIC PARSEABILITY


def get_numeric_parseable_percentage(
    series: pd.Series
) -> float:
    """
    Calculate the percentage of non-null values
    that can be directly parsed as numeric.

    No symbols, commas, percentages, or currency
    signs are removed during this process.
    """

    normalized = normalize_for_inference(series)

    non_null = normalized.dropna()

    if non_null.empty:
        return 0.0

    numeric_values = pd.to_numeric(
        non_null,
        errors="coerce"
    )

    return float(
        numeric_values.notna().mean() * 100
    )


# 4. INTEGER VS FLOAT FOR NUMERIC STRINGS

def infer_numeric_string_type(series: pd.Series) -> str:
    """
    Determine whether a string/object column containing
    numeric values represents integers or floats.

    Returns:
        "integer"
        "float"
        "unknown"
    """

    normalized = normalize_for_inference(series)

    non_null = normalized.dropna()

    if non_null.empty:
        return "unknown"

    numeric_values = pd.to_numeric(
        non_null,
        errors="coerce"
    )

    # Mixed values cannot be confidently classified.
    if numeric_values.isna().any():
        return "unknown"

    # Example:
    # 10, 20, 30 -> integer
    # 10.5, 20.5 -> float
    if (numeric_values % 1 == 0).all():
        return "integer"

    return "float"

# 5. DATETIME PARSEABILITY

def get_datetime_parseable_percentage(
    series: pd.Series
) -> float:
    """
    Calculate the percentage of non-null values
    that can be parsed as datetime.

    The original Series is not modified.
    """

    normalized = normalize_for_inference(series)

    non_null = normalized.dropna()

    if non_null.empty:
        return 0.0

    datetime_values = pd.to_datetime(
        non_null,
        errors="coerce"
    )

    return float(
        datetime_values.notna().mean() * 100
    )


# 6. CASE VARIATION DETECTION

def has_case_variations(series: pd.Series) -> bool:
    """
    Detect whether the column contains values that differ
    only because of letter casing.

    Example:

        "Pune"
        "pune"
        "PUNE"

    Case is NOT changed in the original data.
    """

    normalized = normalize_for_inference(series)

    non_null = normalized.dropna()

    string_values = non_null[
        non_null.map(
            lambda value: isinstance(value, str)
        )
    ]

    if string_values.empty:
        return False

    # Lowercase is used only for comparison.
    case_insensitive_values = string_values.map(
        lambda value: value.lower()
    )

    return (
        case_insensitive_values.nunique()
        < string_values.nunique()
    )

# 7. WHITESPACE DETECTION

def has_whitespace(series: pd.Series) -> bool:
    """
    Detect leading or trailing whitespace
    in string values.

    The original values are not modified.
    """

    non_null = series.dropna()

    string_values = non_null[
        non_null.map(
            lambda value: isinstance(value, str)
        )
    ]

    if string_values.empty:
        return False

    return string_values.map(
        lambda value: value != value.strip()
    ).any()


# 8. EMPTY STRING DETECTION

def has_empty_strings(series: pd.Series) -> bool:
    """
    Detect empty or whitespace-only strings.

    Examples:
        ""
        " "
        "    "

    These are not treated as normal missing values yet.
    They are simply detected and reported.
    """

    non_null = series.dropna()

    string_values = non_null[
        non_null.map(
            lambda value: isinstance(value, str)
        )
    ]

    if string_values.empty:
        return False

    return string_values.map(
        lambda value: value.strip() == ""
    ).any()


# 9. BOOLEAN PARSEABILITY


def get_boolean_parseable_percentage(
    series: pd.Series
) -> float:
    """
    Calculate the percentage of non-null values that
    match common boolean representations.

    Case is ignored only for comparison.

    The original data is not modified.

    Supported representations include:

        True / False
        true / false
        yes / no
        y / n
        1 / 0
    """

    normalized = normalize_for_inference(series)

    non_null = normalized.dropna()

    if non_null.empty:
        return 0.0

    boolean_values = {
        "true",
        "false",
        "yes",
        "no",
        "y",
        "n",
        "1",
        "0"
    }

    def is_boolean(value) -> bool:

        if isinstance(value, bool):
            return True

        if isinstance(value, str):
            return value.lower() in boolean_values

        if isinstance(value, int) and value in {0, 1}:
            return True

        return False

    parseable_count = sum(
        is_boolean(value)
        for value in non_null
    )

    return float(
        (parseable_count / len(non_null)) * 100
    )

# 10. MIXED-TYPE DETECTION

def has_mixed_types(series: pd.Series) -> bool:
    """
    Detect whether a column contains multiple Python-level
    value types.

    Example:

        10
        20
        "unknown"
        40.5

    Such columns may require additional preprocessing.
    """

    non_null = series.dropna()

    if non_null.empty:
        return False

    value_types = non_null.map(
        lambda value: type(value).__name__
    )

    return value_types.nunique() > 1


# 11. CONSTANT COLUMN DETECTION


def is_constant(series: pd.Series) -> bool:
    """
    Determine whether a column contains only one
    unique non-null value.
    """

    non_null = series.dropna()

    if non_null.empty:
        return False

    return non_null.nunique() == 1


# 12. POTENTIAL ID DETECTION

def is_potential_id(series: pd.Series) -> bool:
    """
    Detect whether a column may represent an identifier.

    A potential ID generally has:
        - very high uniqueness
        - relatively few duplicate values
        - non-null values

    This is only an observation.
    It does not guarantee that the column is an ID.
    """

    non_null = series.dropna()

    if non_null.empty:
        return False

    unique_percentage = (
        non_null.nunique()
        / len(non_null)
    ) * 100

    return unique_percentage >= 95.0

# 13. CATEGORICAL VS TEXT

def infer_categorical_or_text(
    series: pd.Series
) -> str:
    """
    Distinguish between categorical and text-like
    string columns.

    Heuristic:
        - Low/moderate cardinality -> categorical
        - High cardinality -> text

    This is an inference, not a final decision.
    """

    normalized = normalize_for_inference(series)

    non_null = normalized.dropna()

    if non_null.empty:
        return "unknown"

    if not non_null.map(
        lambda value: isinstance(value, str)
    ).all():
        return "unknown"

    unique_count = non_null.nunique()

    unique_percentage = (
        unique_count / len(non_null)
    ) * 100

    # Low/moderate cardinality.
    if unique_count <= 50 or unique_percentage <= 10:
        return "categorical"

    return "text"


# 14. MAIN SEMANTIC TYPE INFERENCE


def infer_semantic_type(series: pd.Series) -> str:
    """
    Infer the semantic type of a column.

    The function first trusts reliable Pandas dtypes.
    For object/string columns, it inspects the actual
    values and uses additional evidence.

    Returns one of:

        integer
        float
        boolean
        datetime
        timedelta
        complex
        categorical
        text
        unknown
    """

    basic_type = infer_basic_type(series)

    # Pandas already knows the type.
    if basic_type != "unknown":
        return basic_type

    normalized = normalize_for_inference(series)

    non_null = normalized.dropna()

    if non_null.empty:
        return "unknown"

    numeric_percentage = (
        get_numeric_parseable_percentage(series)
    )

    if numeric_percentage == 100.0:
        return infer_numeric_string_type(series)

    datetime_percentage = (
        get_datetime_parseable_percentage(series)
    )

    if datetime_percentage == 100.0:
        return "datetime"

    boolean_percentage = (
        get_boolean_parseable_percentage(series)
    )

    if boolean_percentage == 100.0:
        return "boolean"

    categorical_or_text = (
        infer_categorical_or_text(series)
    )

    return categorical_or_text
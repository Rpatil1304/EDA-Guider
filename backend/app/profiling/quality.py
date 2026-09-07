import pandas as pd


def get_missing_value_info(
    series: pd.Series
) -> tuple[int, float]:
    """
    Calculate missing-value count and percentage
    for a column.

    Returns:
        (missing_count, missing_percentage)
    """

    missing_count = int(series.isna().sum())

    total_count = len(series)

    if total_count == 0:
        return 0, 0.0

    missing_percentage = (
        missing_count / total_count
    ) * 100

    return (
        missing_count,
        float(missing_percentage)
    )


def get_unique_value_info(
    series: pd.Series
) -> tuple[int, float]:
    """
    Calculate unique-value count and percentage
    for a column.

    Missing values are excluded from the unique count.

    Returns:
        (unique_count, unique_percentage)
    """

    non_null = series.dropna()

    if non_null.empty:
        return 0, 0.0

    unique_count = int(
        non_null.nunique()
    )

    unique_percentage = (
        unique_count / len(non_null)
    ) * 100

    return (
        unique_count,
        float(unique_percentage)
    )


def has_duplicate_values(
    series: pd.Series
) -> bool:
    """
    Check whether a column contains duplicate
    non-null values.
    """

    non_null = series.dropna()

    if non_null.empty:
        return False

    return bool(
        non_null.duplicated().any()
    )


def get_duplicate_row_info(
    df: pd.DataFrame
) -> tuple[int, float]:
    """
    Calculate the number and percentage of
    completely duplicated rows in a DataFrame.

    Returns:
        (duplicate_row_count, duplicate_row_percentage)
    """

    duplicate_count = int(
        df.duplicated().sum()
    )

    total_rows = len(df)

    if total_rows == 0:
        return 0, 0.0

    duplicate_percentage = (
        duplicate_count / total_rows
    ) * 100

    return (
        duplicate_count,
        float(duplicate_percentage)
    )


def get_whitespace_info(
    series: pd.Series
) -> tuple[int, float]:
    """
    Calculate the number and percentage of string values
    containing leading or trailing whitespace.

    The original data is not modified.
    """

    non_null = series.dropna()

    if non_null.empty:
        return 0, 0.0

    string_values = non_null[
        non_null.map(
            lambda value: isinstance(value, str)
        )
    ]

    if string_values.empty:
        return 0, 0.0

    whitespace_mask = string_values.map(
        lambda value: value != value.strip()
    )

    whitespace_count = int(
        whitespace_mask.sum()
    )

    whitespace_percentage = (
        whitespace_count / len(string_values)
    ) * 100

    return (
        whitespace_count,
        float(whitespace_percentage)
    )


def get_empty_string_info(
    series: pd.Series
) -> tuple[int, float]:
    """
    Calculate the number and percentage of empty
    or whitespace-only string values.

    The original data is not modified.
    """

    non_null = series.dropna()

    if non_null.empty:
        return 0, 0.0

    string_values = non_null[
        non_null.map(
            lambda value: isinstance(value, str)
        )
    ]

    if string_values.empty:
        return 0, 0.0

    empty_mask = string_values.map(
        lambda value: value.strip() == ""
    )

    empty_count = int(
        empty_mask.sum()
    )

    empty_percentage = (
        empty_count / len(string_values)
    ) * 100

    return (
        empty_count,
        float(empty_percentage)
    )


def get_outlier_info(
    series: pd.Series
) -> tuple[int, float]:
    """
    Detect statistical outliers in a numeric column
    using the IQR (Interquartile Range) method.

    Returns:
        (outlier_count, outlier_percentage)

    This function only reports outliers.
    It does not remove or modify them.
    """

    if not pd.api.types.is_numeric_dtype(series):
        return 0, 0.0

    non_null = series.dropna()

    if non_null.empty:
        return 0, 0.0

    q1 = non_null.quantile(0.25)
    q3 = non_null.quantile(0.75)

    iqr = q3 - q1

    if iqr == 0:
        return 0, 0.0

    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)

    outlier_mask = (
        (non_null < lower_bound)
        | (non_null > upper_bound)
    )

    outlier_count = int(
        outlier_mask.sum()
    )

    outlier_percentage = (
        outlier_count / len(non_null)
    ) * 100

    return (
        outlier_count,
        float(outlier_percentage)
    )


def get_null_like_count(
    series: pd.Series
) -> int:
    """
    Count values that are likely to represent missing data.

    Actual Pandas missing values are included.
    Empty and whitespace-only strings are also considered
    null-like.

    Common textual missing markers are detected
    case-insensitively.

    The original data is not modified.
    """

    string_missing_values = {
        "",
        "na",
        "n/a",
        "nan",
        "null",
        "none",
        "missing",
    }

    def is_null_like(value) -> bool:

        if pd.isna(value):
            return True

        if isinstance(value, str):
            return (
                value.strip().lower()
                in string_missing_values
            )

        return False

    null_like_mask = series.map(
        is_null_like
    )

    return int(
        null_like_mask.sum()
    )
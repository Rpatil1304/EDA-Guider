from pydantic import BaseModel, Field



# 1. Numeric column statistics
#    Similar to df.describe()


class NumericStatistics(BaseModel):

    count: int = 0

    mean: float | None = None
    median: float | None = None
    std: float | None = None

    minimum: float | None = None
    maximum: float | None = None

    q1: float | None = None
    q3: float | None = None

    skewness: float | None = None
    kurtosis: float | None = None

    # IQR-based outlier information

    iqr: float | None = None
    lower_bound: float | None = None
    upper_bound: float | None = None

    outlier_count: int = 0
    outlier_percentage: float = 0.0


# 2. Categorical column statistics
#    Similar to df.describe(include="object")


class CategoricalStatistics(BaseModel):

    count: int = 0
    unique_count: int = 0

    top: str | None = None
    top_frequency: int = 0
    top_percentage: float = 0.0

    top_categories: dict[str, int] = Field(
        default_factory=dict
    )


# 3. Datetime column statistics


class DatetimeStatistics(BaseModel):

    count: int = 0

    minimum: str | None = None
    maximum: str | None = None

    unique_count: int = 0

    duration_days: float | None = None


# 4. Boolean column statistics


class BooleanStatistics(BaseModel):

    count: int = 0

    true_count: int = 0
    false_count: int = 0

    true_percentage: float = 0.0
    false_percentage: float = 0.0


# 5. General column statistics


class ColumnStatistics(BaseModel):

    name: str
    inferred_type: str

    count: int = 0
    missing_count: int = 0
    missing_percentage: float = 0.0

    unique_count: int = 0
    unique_percentage: float = 0.0

    numeric: NumericStatistics | None = None
    categorical: CategoricalStatistics | None = None
    datetime: DatetimeStatistics | None = None
    boolean: BooleanStatistics | None = None


# 6. Dataset-level statistical information


class StatisticalProfile(BaseModel):

    n_rows: int = 0
    n_cols: int = 0

    numeric_columns: dict[str, NumericStatistics] = Field(
        default_factory=dict
    )

    categorical_columns: dict[str, CategoricalStatistics] = Field(
        default_factory=dict
    )

    datetime_columns: dict[str, DatetimeStatistics] = Field(
        default_factory=dict
    )

    boolean_columns: dict[str, BooleanStatistics] = Field(
        default_factory=dict
    )

    columns: dict[str, ColumnStatistics] = Field(
        default_factory=dict
    )

    correlation_matrix: dict[str, dict[str, float]] = Field(
        default_factory=dict
    )


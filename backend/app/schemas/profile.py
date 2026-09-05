from typing import Any

from pydantic import BaseModel, Field


class ColumnProfile(BaseModel):

    # 1. Basic column information

    name: str
    raw_dtype: str
    inferred_type: str
    row_count: int = 0


    # 2. Missing-value information

    missing_count: int = 0
    missing_percentage: float = 0.0
    null_like_count: int = 0


    # 3. Cardinality / uniqueness information

    unique_count: int = 0
    unique_percentage: float = 0.0


    # 4. Raw data-quality observations

    has_whitespace: bool = False
    has_empty_strings: bool = False
    invalid_parse_count: int = 0


    # 5. Type-conversion / semantic detection information

    numeric_parseable_percentage: float | None = None
    datetime_parseable_percentage: float | None = None
    boolean_parseable_percentage: float | None = None


    # 6. Possible special characteristics

    is_constant: bool = False
    is_potential_id: bool = False


    # 7. Raw-value examples

    sample_values: list[Any] = Field(default_factory=list)


    # 8. Preprocessing-related observations

    preprocessing_flags: list[str] = Field(default_factory=list)
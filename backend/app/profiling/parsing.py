"""Shared, non-mutating parsers used by profiling and preprocessing."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd


_PLAIN_NUMBER = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
_GROUPED_NUMBER = re.compile(
    r"^[+-]?(?:(?:\d{1,3}(?:,\d{3})+)|(?:\d{1,3}(?:,\d{2})*,\d{3}))(?:\.\d+)?$"
)


def parse_numeric_value(value: Any) -> float | int | None:
    """Parse plain or consistently grouped numeric text without guessing units."""

    if pd.isna(value) or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    if not isinstance(value, str):
        return None

    text = value.strip()
    if not (_PLAIN_NUMBER.fullmatch(text) or _GROUPED_NUMBER.fullmatch(text)):
        return None
    normalized = text.replace(",", "")
    try:
        number = float(normalized)
    except ValueError:
        return None
    return int(number) if number.is_integer() else number


def numeric_parse_mask(series: pd.Series) -> pd.Series:
    """Return a boolean mask for values that can safely be parsed as numbers."""

    return series.map(lambda value: parse_numeric_value(value) is not None)


def parse_numeric_series(series: pd.Series) -> pd.Series:
    """Convert safely recognized numeric values and preserve invalid values as NA."""

    return series.map(parse_numeric_value)
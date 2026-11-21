"""Metadata extraction module for clean datasets.

Extracts structured schema, statistical summaries, and sample records
from a clean pandas DataFrame to serve as context for LLM queries and visualizations.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


def _clean_numeric_value(val: Any) -> Optional[float]:
    """Convert numpy or float values to standard Python float, handling NaN/inf."""
    if val is None or pd.isna(val):
        return None
    try:
        f_val = float(val)
        if math.isnan(f_val) or math.isinf(f_val):
            return None
        return round(f_val, 4)
    except (ValueError, TypeError):
        return None


def _clean_int_value(val: Any) -> int:
    """Convert numpy or int values to standard Python int."""
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def _infer_general_type(series: pd.Series) -> str:
    """Infer high-level column type for LLM and visualization understanding."""
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    
    # Check if object column is parseable datetime
    if series.dropna().shape[0] > 0 and series.dtype == "object":
        sample = series.dropna().iloc[:20]
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                pd.to_datetime(sample, errors="raise", format="mixed")
            return "datetime"
        except (ValueError, TypeError, OverflowError):
            pass

    # Check cardinality for text vs categorical
    unique_count = series.nunique(dropna=True)
    total_count = len(series.dropna())
    
    if total_count > 0 and (unique_count / total_count < 0.2 or unique_count <= 25):
        return "categorical"
    
    return "text"


def extract_dataset_metadata(df: pd.DataFrame) -> Dict[str, Any]:
    """Extract comprehensive metadata and statistics from a clean DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        The clean dataset.

    Returns
    -------
    Dict[str, Any]
        Structured metadata including shapes, column types, statistics,
        and sample rows suitable for JSON serialization and LLM context.
    """
    total_rows, total_cols = df.shape
    duplicate_rows = _clean_int_value(df.duplicated().sum())
    total_missing_cells = _clean_int_value(df.isna().sum().sum())
    total_cells = total_rows * total_cols if total_rows and total_cols else 1
    missing_ratio = round((total_missing_cells / total_cells) * 100, 2)

    columns_info: Dict[str, Dict[str, Any]] = {}
    numeric_cols: List[str] = []
    categorical_cols: List[str] = []
    datetime_cols: List[str] = []
    boolean_cols: List[str] = []
    text_cols: List[str] = []

    for col in df.columns:
        series = df[col]
        col_str = str(col)
        general_type = _infer_general_type(series)
        null_count = _clean_int_value(series.isna().sum())
        null_percent = round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
        unique_count = _clean_int_value(series.nunique(dropna=True))

        col_meta: Dict[str, Any] = {
            "name": col_str,
            "pandas_dtype": str(series.dtype),
            "general_type": general_type,
            "null_count": null_count,
            "null_percentage": null_percent,
            "unique_count": unique_count,
            "stats": {},
        }

        if general_type == "numeric":
            numeric_cols.append(col_str)
            clean_series = series.dropna()
            if not clean_series.empty:
                col_meta["stats"] = {
                    "min": _clean_numeric_value(clean_series.min()),
                    "max": _clean_numeric_value(clean_series.max()),
                    "mean": _clean_numeric_value(clean_series.mean()),
                    "median": _clean_numeric_value(clean_series.median()),
                    "std": _clean_numeric_value(clean_series.std()),
                    "q25": _clean_numeric_value(clean_series.quantile(0.25)),
                    "q75": _clean_numeric_value(clean_series.quantile(0.75)),
                    "zeros_count": _clean_int_value((clean_series == 0).sum()),
                }

        elif general_type in ("categorical", "text"):
            if general_type == "categorical":
                categorical_cols.append(col_str)
            else:
                text_cols.append(col_str)
                
            clean_series = series.dropna().astype(str)
            if not clean_series.empty:
                # Top 8 most frequent categories
                top_counts = clean_series.value_counts().head(8).to_dict()
                col_meta["stats"] = {
                    "top_values": {str(k): int(v) for k, v in top_counts.items()},
                    "sample_values": clean_series.sample(min(3, len(clean_series)), random_state=42).tolist(),
                }

        elif general_type == "datetime":
            datetime_cols.append(col_str)
            clean_series = pd.to_datetime(series.dropna(), errors="coerce")
            if not clean_series.empty:
                col_meta["stats"] = {
                    "min_date": str(clean_series.min()),
                    "max_date": str(clean_series.max()),
                }

        elif general_type == "boolean":
            boolean_cols.append(col_str)
            clean_series = series.dropna()
            col_meta["stats"] = {
                "true_count": _clean_int_value((clean_series == True).sum()),
                "false_count": _clean_int_value((clean_series == False).sum()),
            }

        columns_info[col_str] = col_meta

    # Sample records (top 3 rows converted safely to standard python primitives)
    sample_df = df.head(3).copy()
    sample_records: List[Dict[str, Any]] = []
    for _, row in sample_df.iterrows():
        row_dict: Dict[str, Any] = {}
        for col_name, val in row.items():
            if pd.isna(val):
                row_dict[str(col_name)] = None
            elif isinstance(val, (np.integer, int)):
                row_dict[str(col_name)] = int(val)
            elif isinstance(val, (np.floating, float)):
                row_dict[str(col_name)] = _clean_numeric_value(val)
            else:
                row_dict[str(col_name)] = str(val)
        sample_records.append(row_dict)

    return {
        "summary": {
            "total_rows": total_rows,
            "total_columns": total_cols,
            "duplicate_rows": duplicate_rows,
            "total_missing_cells": total_missing_cells,
            "missing_cell_percentage": missing_ratio,
        },
        "column_groups": {
            "numeric": numeric_cols,
            "categorical": categorical_cols,
            "datetime": datetime_cols,
            "boolean": boolean_cols,
            "text": text_cols,
        },
        "columns": columns_info,
        "sample_records": sample_records,
    }

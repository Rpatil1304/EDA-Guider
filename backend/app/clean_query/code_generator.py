"""LLM Code Generator module for clean dataset queries.

Converts natural language queries into executable Pandas/Plotly Python code
using the pre-extracted dataset metadata context.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

from app.llm_client import (
    invoke_gemini_prompt,
    get_model_name as get_default_model,
)


def _format_metadata_for_prompt(metadata: Dict[str, Any]) -> str:
    """Format structured metadata into a concise, readable prompt context."""
    summary = metadata.get("summary", {})
    summary_text = (
        f"Total Rows: {summary.get('total_rows', 0)}, "
        f"Total Columns: {summary.get('total_columns', 0)}, "
        f"Missing Cells: {summary.get('missing_cell_percentage', 0)}%"
    )

    cols = metadata.get("columns", {})
    col_lines = []
    for col_name, info in cols.items():
        g_type = info.get("general_type", "unknown")
        p_dtype = info.get("pandas_dtype", "")
        stats = info.get("stats", {})
        stat_summary = ""
        if g_type == "numeric":
            min_v = stats.get("min")
            max_v = stats.get("max")
            mean_v = stats.get("mean")
            stat_summary = f"(min: {min_v}, max: {max_v}, mean: {mean_v})"
        elif g_type in ("categorical", "text"):
            top_vals = list(stats.get("top_values", {}).keys())[:5]
            if top_vals:
                stat_summary = f"(sample categories: {top_vals})"
        elif g_type == "datetime":
            stat_summary = f"(range: {stats.get('min_date')} to {stats.get('max_date')})"

        col_lines.append(f"- '{col_name}' ({p_dtype}, {g_type}) {stat_summary}")

    sample_rows = json.dumps(metadata.get("sample_records", [])[:2], indent=2)

    return f"""DATASET OVERVIEW:
{summary_text}

COLUMNS & TYPES:
{chr(10).join(col_lines)}

SAMPLE RECORDS (first 2 rows):
{sample_rows}"""


def _clean_code_block(raw_text: str) -> str:
    """Extract clean Python code from LLM markdown response."""
    match = re.search(r"```(?:python)?(.*?)```", raw_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return raw_text.strip()


def generate_python_code(
    user_query: str,
    metadata: Dict[str, Any],
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate executable Python pandas/plotly code from a natural language query.

    Parameters
    ----------
    user_query : str
        User's question or command in natural language.
    metadata : Dict[str, Any]
        Pre-extracted dataset metadata.
    model_name : Optional[str]
        Optional model override.

    Returns
    -------
    Dict[str, Any]
        Dictionary with keys:
        - "code": Executable Python code string.
        - "intent": "calculation", "visualization", or "both".
        - "explanation": Brief explanation of the approach.
        - "chart_type": Type of chart if applicable ("bar", "scatter", "line", "none").
    """
    dataset_context = _format_metadata_for_prompt(metadata)

    system_instruction = """You are an expert Data Analyst and Python programmer.
Given a dataset schema and metadata, your job is to write clean, executable Python code to answer the user's natural language query.

CRITICAL EXECUTION RULES:
1. The DataFrame is ALREADY LOADED into a variable named `df`. DO NOT reload or read files (no pd.read_csv).
2. The DataFrame `df` is already a copy, but write defensive code (e.g., .dropna() when computing correlations or aggregations).
3. Always match the exact column names as defined in the schema.
4. If the query requires a tabular answer, statistical number, or text summary:
   - Assign the final computed result to a variable named `output_result`.
   - `output_result` can be a scalar (int/float/str), a pandas Series, or a pandas DataFrame.
5. If the query asks for or naturally benefits from a chart/visualization:
   - Use `import plotly.express as px` or `import plotly.graph_objects as go`.
   - Create the Plotly figure and assign it to a variable named `fig`.
   - Example: `fig = px.bar(top_df, x='country', y='population', title='Top Countries')`
   - DO NOT call `fig.show()`.
6. Output JSON ONLY in the following format:
```json
{
  "intent": "calculation" | "visualization" | "both",
  "chart_type": "bar" | "scatter" | "line" | "histogram" | "box" | "pie" | "none",
  "explanation": "Brief 1-sentence explanation of what the code does.",
  "code": "Python code here as a single string"
}
```
Do not include any explanation outside of the JSON block.
"""

    prompt = f"""{dataset_context}

USER QUERY:
"{user_query}"

Write the response in the specified JSON structure."""

    raw_text = invoke_gemini_prompt(
        system_instruction=system_instruction,
        user_prompt=prompt,
        temperature=0.0,
        model_name=model_name,
    )
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        # Fallback if wrapped in markdown
        cleaned = _clean_code_block(raw_text)
        try:
            parsed = json.loads(cleaned)
        except Exception:
            parsed = {
                "intent": "calculation",
                "chart_type": "none",
                "explanation": "Extracted code from response.",
                "code": cleaned,
            }

    # Ensure code field has clean python syntax
    if "code" in parsed and isinstance(parsed["code"], str):
        parsed["code"] = _clean_code_block(parsed["code"])

    return parsed


def refine_python_code(
    failed_code: str,
    error_message: str,
    user_query: str,
    metadata: Dict[str, Any],
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Refine and correct previously failed Python code using execution traceback.

    Parameters
    ----------
    failed_code : str
        The code that failed during execution.
    error_message : str
        Error traceback or exception message.
    user_query : str
        Original natural language user query.
    metadata : Dict[str, Any]
        Pre-extracted dataset metadata.
    model_name : Optional[str]
        Optional model override.

    Returns
    -------
    Dict[str, Any]
        Corrected code dictionary matching generate_python_code format.
    """
    dataset_context = _format_metadata_for_prompt(metadata)

    system_instruction = """You are an expert Python debugger and Data Analyst.
A previously generated Python snippet failed to execute against a pandas DataFrame `df`.
Analyze the error message and the schema, and write CORRECTED, working Python code.

CRITICAL RULES:
1. `df` is already loaded in memory.
2. Fix the specific error (e.g. invalid column name, wrong type, or method mismatch).
3. If calculation: assign final output to `output_result`.
4. If chart: create Plotly figure and assign to `fig` (DO NOT call fig.show()).
5. Return JSON ONLY with:
```json
{
  "intent": "calculation" | "visualization" | "both",
  "chart_type": "bar" | "scatter" | "line" | "histogram" | "box" | "pie" | "none",
  "explanation": "Brief explanation of how the bug was fixed.",
  "code": "Corrected Python code here as a single string"
}
```
"""

    prompt = f"""{dataset_context}

USER QUERY:
"{user_query}"

FAILED CODE:
```python
{failed_code}
```

ERROR / TRACEBACK:
{error_message}

Please provide the corrected Python code in the specified JSON structure."""

    raw_text = invoke_gemini_prompt(
        system_instruction=system_instruction,
        user_prompt=prompt,
        temperature=0.0,
        model_name=model_name,
    )
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        cleaned = _clean_code_block(raw_text)
        try:
            parsed = json.loads(cleaned)
        except Exception:
            parsed = {
                "intent": "calculation",
                "chart_type": "none",
                "explanation": "Corrected code extracted.",
                "code": cleaned,
            }

    if "code" in parsed and isinstance(parsed["code"], str):
        parsed["code"] = _clean_code_block(parsed["code"])

    return parsed


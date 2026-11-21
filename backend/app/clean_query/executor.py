"""Safe code execution sandbox with AST validation, error handling, and self-correction.

Executes generated Python code against an isolated DataFrame copy and
manages automated retry loops if runtime or syntax errors occur.
"""

from __future__ import annotations

import ast
import contextlib
import datetime
import io
import json
import math
import re
import traceback
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.clean_query.code_generator import refine_python_code


# Strict whitelist: Only these verified data analysis libraries are permitted.
# Any unknown, third-party, or extraneous module will be blocked.
ALLOWED_MODULES = {
    "pandas",
    "numpy",
    "plotly",
    "math",
    "datetime",
    "re",
}

DISALLOWED_CALLS = {
    "open", "eval", "exec", "compile", "__import__", "breakpoint", "input"
}


class CodeSecurityError(Exception):
    """Raised when code violates security policies."""
    pass


def validate_code_ast(code: str) -> None:
    """Validate Python code against unauthorized imports or dangerous builtins.

    Parameters
    ----------
    code : str
        The Python code string to inspect.

    Raises
    ------
    CodeSecurityError
        If forbidden modules or functions are detected.
    SyntaxError
        If the code is invalid Python syntax.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise SyntaxError(f"Syntax error in generated code: {e}") from e

    for node in ast.walk(tree):
        # Strict allowlist check: block any library not in ALLOWED_MODULES
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_pkg = alias.name.split(".")[0]
                if root_pkg not in ALLOWED_MODULES:
                    raise CodeSecurityError(
                        f"Security error: import of unknown or unauthorized library '{alias.name}' is prohibited. "
                        f"Only {sorted(ALLOWED_MODULES)} are allowed."
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_pkg = node.module.split(".")[0]
                if root_pkg not in ALLOWED_MODULES:
                    raise CodeSecurityError(
                        f"Security error: import from unknown or unauthorized library '{node.module}' is prohibited. "
                        f"Only {sorted(ALLOWED_MODULES)} are allowed."
                    )

        # Disallow forbidden function calls
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in DISALLOWED_CALLS:
                raise CodeSecurityError(f"Security error: call to '{node.func.id}()' is prohibited.")


def _serialize_output(val: Any) -> Tuple[Any, str]:
    """Serialize output_result into JSON-safe format and human-readable string."""
    if val is None:
        return None, "No direct result object assigned."

    if isinstance(val, pd.DataFrame):
        # Truncate if very large
        df_clean = val.copy()
        if len(df_clean) > 100:
            df_clean = df_clean.head(100)
        
        # Replace NaN with None for clean JSON serialization
        records = df_clean.where(pd.notnull(df_clean), None).to_dict(orient="records")
        return {
            "type": "dataframe",
            "columns": [str(c) for c in df_clean.columns],
            "total_rows": len(val),
            "data": records,
        }, df_clean.to_string(index=False)

    if isinstance(val, pd.Series):
        s_clean = val.copy()
        if len(s_clean) > 100:
            s_clean = s_clean.head(100)
        s_clean = s_clean.where(pd.notnull(s_clean), None)
        return {
            "type": "series",
            "name": str(val.name or "Series"),
            "data": s_clean.to_dict(),
        }, s_clean.to_string()

    if isinstance(val, (np.integer, int)):
        return int(val), str(val)

    if isinstance(val, (np.floating, float)):
        if math.isnan(val) or math.isinf(val):
            return None, "NaN"
        return round(float(val), 4), str(round(float(val), 4))

    if isinstance(val, (bool, np.bool_)):
        return bool(val), str(bool(val))

    if isinstance(val, (list, tuple)):
        return list(val), str(val)

    if isinstance(val, dict):
        return val, str(val)

    return str(val), str(val)


def _execute_code_once(
    code: str,
    df: pd.DataFrame,
) -> Dict[str, Any]:
    """Perform a single isolated execution run.

    Raises exceptions if code fails.
    """
    validate_code_ast(code)

    # Isolated DataFrame copy
    df_isolated = df.copy(deep=True)

    # Safe restricted namespace
    builtins_dict = __builtins__ if isinstance(__builtins__, dict) else vars(__builtins__)
    safe_builtins = {
        name: builtins_dict[name]
        for name in builtins_dict
        if name not in DISALLOWED_CALLS and not name.startswith("_")
    }

    # Custom safe import that strictly enforces ALLOWED_MODULES
    def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
        root = name.split(".")[0]
        if root not in ALLOWED_MODULES:
            raise CodeSecurityError(
                f"Security error: import of unknown or unauthorized library '{name}' is prohibited."
            )
        return __import__(name, globals, locals, fromlist, level)

    safe_builtins["__import__"] = safe_import

    local_namespace: Dict[str, Any] = {
        "df": df_isolated,
        "pd": pd,
        "np": np,
        "px": px,
        "go": go,
        "math": math,
        "re": re,
        "datetime": datetime,
        "__builtins__": safe_builtins,
    }

    stdout_capture = io.StringIO()

    with contextlib.redirect_stdout(stdout_capture):
        exec(code, local_namespace)

    stdout_text = stdout_capture.getvalue().strip()

    # Extract results
    raw_result = local_namespace.get("output_result")
    raw_fig = local_namespace.get("fig")

    serialized_result, string_repr = _serialize_output(raw_result)

    # Plotly figure extraction
    figure_dict = None
    has_figure = False
    if raw_fig is not None and isinstance(raw_fig, (go.Figure,)):
        has_figure = True
        try:
            # json.loads(raw_fig.to_json()) produces a 100% JSON-compliant dictionary
            # with no non-serializable objects (numpy arrays, dates, properties)
            figure_dict = json.loads(raw_fig.to_json())
        except Exception:
            try:
                figure_dict = raw_fig.to_dict()
            except Exception:
                figure_dict = None

    return {
        "status": "success",
        "result_data": serialized_result,
        "result_string": string_repr,
        "stdout": stdout_text,
        "has_figure": has_figure,
        "figure": figure_dict,
    }


def execute_with_self_correction(
    code: str,
    df: pd.DataFrame,
    user_query: str,
    metadata: Dict[str, Any],
    max_retries: int = 2,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute Python code against df with defensive exception handling and self-correction.

    Parameters
    ----------
    code : str
        Initial Python code to execute.
    df : pd.DataFrame
        Clean dataset.
    user_query : str
        Original natural language query from user.
    metadata : Dict[str, Any]
        Pre-extracted metadata dictionary.
    max_retries : int
        Number of automated retry attempts using LLM self-healing.
    model_name : Optional[str]
        Optional Gemini model name.

    Returns
    -------
    Dict[str, Any]
        Execution summary with results, figure data, executed code, and retry history.
    """
    current_code = code
    attempts: List[Dict[str, Any]] = []

    for attempt_idx in range(max_retries + 1):
        try:
            run_output = _execute_code_once(current_code, df)
            return {
                "status": "success",
                "final_code": current_code,
                "attempts_count": attempt_idx + 1,
                "history": attempts,
                "result_data": run_output["result_data"],
                "result_string": run_output["result_string"],
                "stdout": run_output["stdout"],
                "has_figure": run_output["has_figure"],
                "figure": run_output["figure"],
                "error": None,
            }

        except Exception as exc:
            error_trace = traceback.format_exc()
            error_msg = f"{type(exc).__name__}: {str(exc)}"
            
            attempts.append({
                "attempt": attempt_idx + 1,
                "code": current_code,
                "error": error_msg,
            })

            # If we still have retries left, ask LLM to refine the code
            if attempt_idx < max_retries:
                try:
                    refinement = refine_python_code(
                        failed_code=current_code,
                        error_message=error_msg,
                        user_query=user_query,
                        metadata=metadata,
                        model_name=model_name,
                    )
                    refined_code = refinement.get("code")
                    if refined_code and refined_code.strip() != current_code.strip():
                        current_code = refined_code
                        continue
                except Exception as refine_exc:
                    attempts.append({
                        "attempt": attempt_idx + 1,
                        "refine_error": f"Self-correction call failed: {refine_exc}",
                    })
                    break

            # If retries exhausted or self-correction failed
            return {
                "status": "error",
                "final_code": current_code,
                "attempts_count": attempt_idx + 1,
                "history": attempts,
                "result_data": None,
                "result_string": None,
                "stdout": None,
                "has_figure": False,
                "figure": None,
                "error": error_msg,
                "traceback": error_trace,
            }

    return {
        "status": "error",
        "final_code": current_code,
        "attempts_count": len(attempts),
        "history": attempts,
        "result_data": None,
        "result_string": None,
        "stdout": None,
        "has_figure": False,
        "figure": None,
        "raw_figure": None,
        "error": "Execution failed after maximum retries.",
    }

"""Unified service pipeline for the Clean dataset Q&A feature.

Orchestrates metadata extraction, code generation, sandboxed execution,
and natural language response synthesis.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import pandas as pd

from app.clean_query.metadata_extractor import extract_dataset_metadata
from app.clean_query.code_generator import generate_python_code
from app.clean_query.executor import execute_with_self_correction
from app.clean_query.answer_generator import generate_natural_language_answer


def process_clean_query(
    df: pd.DataFrame,
    user_query: str,
    metadata: Optional[Dict[str, Any]] = None,
    max_retries: int = 2,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute end-to-end natural language query on a clean DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        The clean dataset.
    user_query : str
        User's question in natural language.
    metadata : Optional[Dict[str, Any]]
        Pre-extracted metadata dictionary (if cached, otherwise computed on the fly).
    max_retries : int
        Number of automated retry attempts on code failure.
    model_name : Optional[str]
        Optional Gemini model name override.

    Returns
    -------
    Dict[str, Any]
        Complete response payload including natural language answer,
        executed code, result data, and figure.
    """
    if df is None or df.empty:
        return {
            "status": "error",
            "query": user_query,
            "answer": "No dataset is currently loaded. Please upload a dataset first.",
            "error": "DataFrame is empty or None.",
        }

    # 1. Metadata extraction (use cached if passed, else extract)
    if metadata is None:
        try:
            metadata = extract_dataset_metadata(df)
        except Exception as exc:
            return {
                "status": "error",
                "query": user_query,
                "answer": f"Failed to extract dataset metadata: {exc}",
                "error": str(exc),
            }

    # 2. LLM Code Generation
    try:
        code_plan = generate_python_code(
            user_query=user_query,
            metadata=metadata,
            model_name=model_name,
        )
    except Exception as exc:
        return {
            "status": "error",
            "query": user_query,
            "answer": f"Failed to generate code for your query: {exc}",
            "error": str(exc),
        }

    generated_code = code_plan.get("code", "")
    intent = code_plan.get("intent", "calculation")
    chart_type = code_plan.get("chart_type", "none")

    # 3. Safe Execution with Self-Correction
    execution_result = execute_with_self_correction(
        code=generated_code,
        df=df,
        user_query=user_query,
        metadata=metadata,
        max_retries=max_retries,
        model_name=model_name,
    )

    # 4. Natural Language Synthesis
    try:
        answer_text = generate_natural_language_answer(
            user_query=user_query,
            execution_result=execution_result,
            metadata=metadata,
            model_name=model_name,
        )
    except Exception as exc:
        answer_text = execution_result.get("result_string") or "Query executed successfully."

    return {
        "status": execution_result.get("status", "error"),
        "query": user_query,
        "answer": answer_text,
        "intent": intent,
        "chart_type": chart_type,
        "code": execution_result.get("final_code", generated_code),
        "result_data": execution_result.get("result_data"),
        "result_string": execution_result.get("result_string"),
        "has_figure": execution_result.get("has_figure", False),
        "figure": execution_result.get("figure"),
        "attempts_count": execution_result.get("attempts_count", 1),
        "error": execution_result.get("error"),
    }

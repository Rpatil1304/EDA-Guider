"""Privacy-safe input preparation for the future LangChain agent."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pandas as pd


_SENSITIVE_PROFILE_FIELDS = {
    "sample_values",
    "outlier_values",
}


def _without_dataset_values(value: Any) -> Any:
    """Remove raw-value payloads while retaining aggregate evidence."""

    if isinstance(value, dict):
        return {
            str(key): _without_dataset_values(item)
            for key, item in value.items()
            if key not in _SENSITIVE_PROFILE_FIELDS
            and key not in {"html", "cleaned_dataframe"}
        }
    if isinstance(value, list):
        return [_without_dataset_values(item) for item in value]
    if isinstance(value, tuple):
        return [_without_dataset_values(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, TypeError):
            pass
    return str(value)


def build_llm_evidence_input(pipeline_result: dict[str, Any]) -> dict[str, Any]:
    """Build the structured, dataset-value-free input for LangChain.

    The function accepts the result returned by the preprocessing pipeline and
    never includes the DataFrame, YData HTML, sample values, or outlier values.
    It retains aggregate profiling metrics, preprocessing decisions, audit
    measurements, validation state, exclusions, and downstream handoff data.
    """

    if not isinstance(pipeline_result, dict):
        raise TypeError("pipeline_result must be a dictionary.")

    summary = pipeline_result.get("preprocessing_summary_report") or {}
    evidence = {
        "evidence_version": "1.0",
        "privacy": {
            "raw_dataset_values_included": False,
            "dataframe_included": False,
            "profiling_html_included": False,
            "removed_fields": sorted(_SENSITIVE_PROFILE_FIELDS | {"html", "cleaned_dataframe"}),
        },
        "dataset": {
            "name": (pipeline_result.get("ingestion_report") or {}).get("file_name"),
            "status": pipeline_result.get("status"),
        },
        "ingestion": pipeline_result.get("ingestion_report"),
        "structure": pipeline_result.get("structural_report"),
        "raw_profile": pipeline_result.get("raw_profile_report"),
        "preprocessing_plan": pipeline_result.get("preprocessing_plan"),
        "execution_log": pipeline_result.get("execution_log"),
        "cleaned_profile": summary.get("cleaned_profile"),
        "preprocessing_summary": summary,
        "downstream_handoff": summary.get("downstream_handoff"),
        "raw_ydata_report": {
            "status": (pipeline_result.get("raw_ydata_profile_report") or {}).get("status"),
        },
        "cleaned_ydata_report": {
            "status": (pipeline_result.get("cleaned_ydata_profile_report") or {}).get("status"),
        },
    }
    return _without_dataset_values(deepcopy(evidence))

class Agent:
    """AI agent for EDA automation"""
    
    def __init__(self):
        self.decisions = []
    
    def analyze(self, data_profile: dict) -> dict:
        """Analyze data and make decisions"""
        # Agent logic
        return {'decisions': self.decisions}

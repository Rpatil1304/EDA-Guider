import pandas as pd

from app.preprocessing.preprocessor import execute_preprocessing_plan
from app.preprocessing.raw_rule_engine import generate_preprocessing_plan
from app.preprocessing.summary import (
    build_preprocessing_summary_report,
    run_preprocessing_stage,
)
from app.profiling.raw_profiler import profile_raw_dataframe


def test_summary_compares_raw_and_cleaned_profiles():
    raw = pd.DataFrame(
        {
            "customer_id": ["C001", "C002", "C003"],
            "amount": ["10", "20", "30"],
            "label": ["YES", "no", "YES"],
        }
    )
    raw_profile = profile_raw_dataframe(raw)
    plan = generate_preprocessing_plan(raw, raw_profile)
    cleaned, execution_log = execute_preprocessing_plan(raw, plan)

    summary = build_preprocessing_summary_report(
        raw_profile,
        cleaned,
        execution_log,
    )

    amount = next(item for item in summary["columns"] if item["column_after"] == "amount")
    assert summary["report_type"] == "preprocessing_summary"
    assert summary["raw_profile"]["profile_type"] == "raw"
    assert summary["cleaned_profile"]["profile_type"] == "cleaned"
    assert amount["changes"]["dtype"]["before"] == "str"
    assert amount["changes"]["dtype"]["after"] in {"int64", "Int64"}
    assert amount["changes"]["dtype"]["changed"] is True
    assert amount["actions"]
    assert summary["summary"]["execution_log_count"] == len(execution_log)


def test_summary_preserves_duplicate_raw_columns_by_position():
    raw = pd.DataFrame([["A", "1"]], columns=["value", "value"])
    raw_profile = profile_raw_dataframe(raw)
    cleaned = raw.copy()
    cleaned.columns = ["value", "value_2"]
    log = [
        {
            "columns": ["value_2"],
            "action": "detect_duplicate_columns",
            "status": "executed",
            "reason": "renamed",
        }
    ]

    summary = build_preprocessing_summary_report(raw_profile, cleaned, log)

    assert [item["column_before"] for item in summary["columns"]] == [
        "value",
        "value",
    ]
    assert [item["column_after"] for item in summary["columns"]] == [
        "value",
        "value_2",
    ]
    assert summary["raw_profile"]["columns"][1]["name"] == "value"


def test_preprocessing_stage_returns_cleaned_data_and_final_artifact():
    raw = pd.DataFrame({"label": ["YES", "no"]})
    raw_profile = profile_raw_dataframe(raw)
    plan = generate_preprocessing_plan(raw, raw_profile)

    cleaned, summary = run_preprocessing_stage(raw, raw_profile, plan)

    assert cleaned["label"].tolist() == [True, False]
    assert summary["report_type"] == "preprocessing_summary"
    assert summary["execution_log"]

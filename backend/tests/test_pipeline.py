from io import BytesIO

import pandas as pd

from app.preprocessing.pipeline import run_preprocessing_pipeline


_REQUIRED_KEYS = {
    "status",
    "ingestion_report",
    "structural_report",
    "raw_profile_report",
    "preprocessing_plan",
    "execution_log",
    "preprocessing_summary_report",
    "cleaned_dataframe",
    "pipeline_error",
}


def test_run_preprocessing_pipeline_returns_all_stage_outputs():
    uploaded = BytesIO(
        b"customer_id,amount,active,label\n"
        b"C001,10,yes,YES\n"
        b"C002,20,no,no\n"
    )
    uploaded.name = "sample.csv"

    result = run_preprocessing_pipeline(uploaded)

    assert set(result) == _REQUIRED_KEYS
    assert result["status"] == "success"
    assert result["pipeline_error"] is None
    assert result["ingestion_report"]["status"] == "success"
    assert result["structural_report"]["status"] == "success"
    assert result["raw_profile_report"]["profile_type"] == "raw"
    assert result["preprocessing_plan"]["source"] == "raw_profile_rule_engine"
    assert isinstance(result["execution_log"], list)
    assert result["preprocessing_summary_report"]["report_type"] == "preprocessing_summary"
    assert isinstance(result["cleaned_dataframe"], pd.DataFrame)
    assert result["cleaned_dataframe"]["active"].tolist() == [True, False]


def test_pipeline_reports_null_like_values_without_replacing_them():
    uploaded = BytesIO(
        b"name,notes\n"
        b"A,NA\n"
        b"B,\n"
        b"C,ok\n"
    )
    uploaded.name = "nulls.csv"

    result = run_preprocessing_pipeline(uploaded)

    null_summary = result["raw_profile_report"]["null_summary"]
    notes_profile = result["raw_profile_report"]["columns"][1]
    assert null_summary["actual_null_count"] == 0
    assert null_summary["null_like_count"] == 2
    assert notes_profile["null_like_breakdown"]["na"] == 1
    assert notes_profile["null_like_breakdown"][""] == 1
    assert result["cleaned_dataframe"]["notes"].tolist() == ["NA", "", "ok"]


def test_run_preprocessing_pipeline_stops_with_structured_ingestion_error():
    uploaded = BytesIO(b"not a supported dataset")
    uploaded.name = "sample.unsupported"

    result = run_preprocessing_pipeline(uploaded)

    assert set(result) == _REQUIRED_KEYS
    assert result["status"] == "error"
    assert result["cleaned_dataframe"] is None
    assert result["preprocessing_summary_report"] is None
    assert result["pipeline_error"]["stage"] == "ingestion"
    assert result["pipeline_error"]["message"]

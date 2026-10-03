from io import BytesIO

import pandas as pd

from app.preprocessing.pipeline import run_preprocessing_pipeline
from app.reporting import generate_eda_guide_report


_REQUIRED_KEYS = {
    "status",
    "ingestion_report",
    "raw_ydata_profile_report",
    "cleaned_ydata_profile_report",
    "structural_report",
    "raw_profile_report",
    "preprocessing_plan",
    "execution_log",
    "preprocessing_summary_report",
    "cleaned_dataframe",
    "pipeline_error",
    "statistical_profile",
    "visualization_recommendations",
    "visualization_evidence",
    "visualization_evidence_groups",
    "llm_visualization_validation",
    "eda_report_evidence",
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
    assert result["status"] == "success", result["pipeline_error"]
    assert result["pipeline_error"] is None
    assert result["ingestion_report"]["status"] == "success"
    assert result["structural_report"]["status"] == "success"
    assert result["raw_profile_report"]["profile_type"] == "raw"
    assert result["preprocessing_plan"]["source"] == "raw_profile_rule_engine"
    assert isinstance(result["execution_log"], list)
    assert result["preprocessing_summary_report"]["report_type"] == "preprocessing_summary"
    assert isinstance(result["cleaned_dataframe"], pd.DataFrame)
    assert result["cleaned_dataframe"]["active"].tolist() == [True, False]
    assert result["preprocessing_summary_report"]["raw_snapshot_unchanged"] is True
    assert result["preprocessing_summary_report"]["summary"]["action_status_counts"]


def test_pipeline_reports_but_preserves_null_like_values():
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


def test_pipeline_converts_grouped_numeric_values_without_data_loss():
    uploaded = BytesIO(
        b"country,population_per_sq_km\nAustria,106.3\nMalta,1610\n"
    )
    uploaded.name = "grouped.csv"

    result = run_preprocessing_pipeline(uploaded)

    assert result["status"] == "success"
    assert result["cleaned_dataframe"]["population_per_sq_km"].tolist() == [106.3, 1610.0], result
    assert result["cleaned_dataframe"]["population_per_sq_km"].notna().all()


def test_identical_value_columns_are_retained_and_marked_for_review():
    uploaded = BytesIO(
        b"first,second,value\nA,A,1\nB,B,2\n"
    )
    uploaded.name = "duplicate_values.csv"

    result = run_preprocessing_pipeline(uploaded)

    assert result["status"] == "success"
    assert result["structural_report"]["duplicate_value_columns"] == [["first", "second"]]
    review_log = [
        entry for entry in result["execution_log"]
        if entry["action"] == "review_duplicate_column"
    ]
    assert review_log
    assert all(entry["status"] == "needs_review" for entry in review_log)
    assert result["cleaned_dataframe"].columns.tolist() == ["first", "second", "value"]


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


def test_eda_guide_report_contains_completed_stages_and_next_steps(tmp_path):
    uploaded = BytesIO(b"name,amount\nA,10\nB,20\n")
    uploaded.name = "sample.csv"
    result = run_preprocessing_pipeline(uploaded)
    output_path = tmp_path / "eda_report.md"

    report = generate_eda_guide_report(result, output_path)

    assert output_path.read_text(encoding="utf-8") == report
    assert "## Part 1 - File ingestion" in report
    assert "## Part 6 - Before-and-after summary" in report
    assert "## Part 8 - Next EDA steps" in report
    assert "Visualization recommendations" in report
    assert "Semantic type" in report
    assert "Action status counts" in report
    assert "Raw snapshot unchanged" in report
    assert "Downstream handoff" in report

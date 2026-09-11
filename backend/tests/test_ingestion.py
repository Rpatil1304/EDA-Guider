from io import BytesIO

import pandas as pd

from app.ingestion.loader import load_file
from app.profiling.raw_profiler import profile_raw_dataframe
from app.ingestion.structural import validate_structure


def test_load_csv_and_validate_structure():
    file_input = BytesIO(b"value,value,city\n1,2,Paris\n")
    file_input.name = "sample.csv"

    df, report = load_file(file_input)

    assert report["status"] == "success"
    assert report["delimiter"] == ","
    assert report["structural"]["duplicate_columns"] == ["value"]
    assert report["raw_profile"]["columns"][0]["name"] == "value"
    assert report["raw_profile"]["columns"][1]["name"] == "value"
    assert report["raw_profile"]["null_summary"]["total_missing_count"] == 0
    assert "preprocessing_plan" in report
    assert list(df.columns) == ["value", "value_2", "city"]
    assert df.iloc[0].to_dict() == {
        "value": 1,
        "value_2": 2,
        "city": "Paris",
    }


def test_load_excel():
    file_input = BytesIO()
    pd.DataFrame({"product": ["A"], "sales": [100]}).to_excel(
        file_input,
        index=False,
        engine="openpyxl",
    )
    file_input.name = "sample.xlsx"

    df, report = load_file(file_input)

    assert report["status"] == "success"
    assert report["file_type"] == "xlsx"
    assert df.to_dict("records") == [{"product": "A", "sales": 100}]


def test_structural_validation_reports_fatal_empty_dataframe():
    df, report = validate_structure(pd.DataFrame())

    assert df is None
    assert report["status"] == "error"
    assert report["fatal"] is True
    assert report["errors"][0]["type"] == "EmptyStructureError"


def test_structural_validation_warns_for_single_row_and_column():
    df, report = validate_structure(pd.DataFrame({"only": [1]}))

    assert df is not None
    assert report["status"] == "success"
    assert len(report["warnings"]) == 2


def test_raw_profile_reports_metrics_warnings_and_does_not_mutate():
    raw = pd.DataFrame(
        {
            "identifier": range(10),
            "constant": ["x"] * 10,
            "missing": [None] * 6 + ["ok"] * 4,
        }
    )
    original = raw.copy(deep=True)

    report = profile_raw_dataframe(raw)

    assert report["profile_type"] == "raw"
    assert report["row_count"] == 10
    assert report["columns"][0]["dtype"] == "int64"
    assert report["columns"][2]["null_percentage"] == 60.0
    assert report["null_summary"]["actual_null_count"] == 6
    assert report["null_summary"]["total_missing_percentage"] == 20.0
    assert report["columns"][0]["unique_count"] == 10
    assert report["columns"][0]["sample_values"] == [0, 1, 2, 3, 4]
    assert any(item["type"] == "high_cardinality" for item in report["warnings"])
    assert any(item["type"] == "constant_column" for item in report["warnings"])
    assert raw.equals(original)


def test_preprocessing_plan_uses_raw_profile_evidence():
    raw = pd.DataFrame(
        {
            "customer_id": ["C001", "C002", "C003"],
            "age": [25, 30, 35],
            "active": ["yes", "no", "yes"],
            "notes": [" hello ", "NA", ""],
        }
    )
    from app.preprocessing.raw_rule_engine import (
        generate_preprocessing_plan_from_raw_profile,
    )

    profile = profile_raw_dataframe(raw)
    plan = generate_preprocessing_plan_from_raw_profile(raw, profile)

    actions = {(action.action, action.columns[0]) for action in plan.actions}
    assert ("preserve_identifier", "customer_id") in actions
    assert ("strip_whitespace", "notes") in actions
    assert ("replace_null_like", "notes") in actions
    assert ("replace_empty_strings", "notes") in actions
    assert ("convert_to_boolean", "active") in actions
    assert all(0 <= action.confidence <= 1 for action in plan.actions)


def test_grouped_numeric_values_are_profiled_as_numeric():
    from app.profiling.parsing import parse_numeric_value

    assert parse_numeric_value("1,610") == 1610
    assert parse_numeric_value("89,17,000") == 8917000
    assert parse_numeric_value("1,2,3") is None


def test_exported_index_column_is_reported_for_review():
    file_input = BytesIO(b",name\n0,A\n1,B\n")
    file_input.name = "indexed.csv"

    df, report = load_file(file_input)

    assert df is not None
    assert report["structural"]["index_like_columns"] == [""]
    assert any("Index-like columns" in warning for warning in report["structural"]["warnings"])

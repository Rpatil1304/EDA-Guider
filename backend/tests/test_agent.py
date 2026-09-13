# Test suite for agent module
import pandas as pd

from app.agent.agent import build_llm_evidence_input

def test_agent_analysis():
    """Test agent analysis"""
    pass

def test_decision_parser():
    """Test decision parsing"""
    pass


def test_llm_evidence_input_excludes_dataset_values_and_keeps_aggregates():
    result = {
        "status": "success",
        "ingestion_report": {"file_name": "sample.csv", "rows": 2},
        "structural_report": {"status": "success"},
        "raw_profile_report": {
            "columns": [{
                "name": "amount",
                "dtype": "str",
                "sample_values": ["secret-value"],
                "outlier_values": [999],
                "unique_count": 2,
            }]
        },
        "preprocessing_plan": {"actions": []},
        "execution_log": [],
        "preprocessing_summary_report": {
            "cleaned_profile": {"columns": [{"name": "amount", "dtype": "float64"}]},
            "downstream_handoff": {"eligible_columns": ["amount"]},
        },
        "raw_ydata_profile_report": {"status": "generated", "html": "private html"},
        "cleaned_ydata_profile_report": {"status": "generated"},
        "cleaned_dataframe": pd.DataFrame({"amount": [1, 2]}),
    }

    evidence = build_llm_evidence_input(result)
    serialized = str(evidence)

    assert evidence["privacy"]["raw_dataset_values_included"] is False
    assert evidence["raw_profile"]["columns"][0]["unique_count"] == 2
    assert "secret-value" not in serialized
    assert "private html" not in serialized
    assert "cleaned_dataframe" not in evidence
    assert "html" not in evidence["raw_ydata_report"]

import pandas as pd

from app.preprocessing.preprocessor import execute_preprocessing_plan
from app.schemas.preprocessing import PreprocessingAction, PreprocessingPlan


def make_plan(*actions: PreprocessingAction) -> PreprocessingPlan:
    return PreprocessingPlan(
        actions=list(actions),
        reasoning="test plan",
        source="test",
    )


def test_execute_plan_uses_copy_fixed_order_and_logs_effects():
    raw = pd.DataFrame(
        {
            "name": [" Ana ", "Bob", "NA"],
            "age": ["25", "30", "35"],
            "label": ["YES", "no", "YES"],
        }
    )
    original = raw.copy(deep=True)
    plan = make_plan(
        PreprocessingAction(
            columns=["label"], action="classify_as_categorical", confidence=0.9, reason="test"
        ),
        PreprocessingAction(
            columns=["label"], action="normalize_case", confidence=0.9, reason="test"
        ),
        PreprocessingAction(
            columns=["age"], action="convert_to_numeric", confidence=0.95, reason="test"
        ),
    )

    cleaned, log = execute_preprocessing_plan(raw, plan)

    assert raw.equals(original)
    assert cleaned["name"].iloc[0] == "Ana"
    assert cleaned["name"].iloc[1] == "Bob"
    assert cleaned["name"].iloc[2] == "NA"
    assert str(cleaned["age"].dtype) in {"int64", "Int64"}
    assert cleaned["label"].tolist() == ["yes", "no", "yes"]
    classification_log = next(
        entry for entry in log if entry["action"] == "classify_as_categorical"
    )
    assert classification_log["status"] == "executed"
    assert classification_log["values_changed"] == 0
    assert [entry["action"] for entry in log[:3]] == [
        "strip_whitespace",
        "strip_whitespace",
        "strip_whitespace",
    ]
    assert any(
        entry["action"] == "convert_to_numeric"
        and entry["status"] == "executed"
        and "null_percentage_before" in entry
        for entry in log
    )


def test_conversion_is_rejected_and_reverted_when_data_loss_is_too_high():
    raw = pd.DataFrame({"amount": ["10", "bad", "20"]})
    plan = make_plan(
        PreprocessingAction(
            columns=["amount"], action="convert_to_numeric", confidence=0.95, reason="test"
        )
    )

    cleaned, log = execute_preprocessing_plan(raw, plan)

    assert cleaned["amount"].tolist() == ["10", "bad", "20"]
    conversion_log = next(entry for entry in log if entry["action"] == "convert_to_numeric")
    assert conversion_log["status"] == "rejected"
    assert conversion_log["null_percentage_before"] == 0.0
    assert conversion_log["null_percentage_after"] > 30.0


def test_low_confidence_conversion_is_skipped_for_manual_review():
    raw = pd.DataFrame({"amount": ["10", "unknown"]})
    plan = make_plan(
        PreprocessingAction(
            columns=["amount"], action="convert_to_numeric", confidence=0.5, reason="test"
        )
    )

    cleaned, log = execute_preprocessing_plan(raw, plan)

    assert cleaned.equals(raw)
    conversion_log = next(entry for entry in log if entry["action"] == "convert_to_numeric")
    assert conversion_log["status"] == "skipped"
    assert "manual review" in conversion_log["reason"]


def test_duplicate_rows_are_reported_not_removed():
    raw = pd.DataFrame({"value": [1, 1, 2]})

    cleaned, log = execute_preprocessing_plan(raw, make_plan())

    assert len(cleaned) == 3
    duplicate_log = next(entry for entry in log if entry["action"] == "detect_duplicate_rows")
    assert duplicate_log["status"] == "executed"
    assert duplicate_log["duplicate_row_count"] == 2


def test_datetime_conversion_is_lossless_and_logged():
    raw = pd.DataFrame({"created_at": ["2025-01-01", "2025-02-01"]})
    plan = make_plan(
        PreprocessingAction(
            columns=["created_at"],
            action="convert_to_datetime",
            confidence=0.95,
            reason="datetime test",
        )
    )

    cleaned, log = execute_preprocessing_plan(raw, plan)

    assert str(cleaned["created_at"].dtype).startswith("datetime64")
    conversion_log = next(entry for entry in log if entry["action"] == "convert_to_datetime")
    assert conversion_log["status"] == "executed"
    assert conversion_log["invalid_non_null_count"] == 0
    assert conversion_log["timezone_policy"] == "utc"


def test_datetime_conversion_rejects_excessive_invalid_values():
    raw = pd.DataFrame({"created_at": ["2025-01-01", "invalid", "invalid"]})
    plan = make_plan(
        PreprocessingAction(
            columns=["created_at"],
            action="convert_to_datetime",
            confidence=0.95,
            reason="invalid date test",
        )
    )

    cleaned, log = execute_preprocessing_plan(raw, plan)

    assert cleaned["created_at"].tolist() == raw["created_at"].tolist()
    conversion_log = next(entry for entry in log if entry["action"] == "convert_to_datetime")
    assert conversion_log["status"] == "rejected"
    assert conversion_log["invalid_non_null_count"] == 2


def test_ambiguous_numeric_dates_require_review():
    raw = pd.DataFrame({"event_date": ["01/02/2025", "02/03/2025"]})
    from app.preprocessing.raw_rule_engine import generate_preprocessing_plan
    from app.profiling.raw_profiler import profile_raw_dataframe

    plan = generate_preprocessing_plan(raw, profile_raw_dataframe(raw))
    assert [action.action for action in plan.actions] == [
        "review_ambiguous_date_format"
    ]

    cleaned, log = execute_preprocessing_plan(raw, plan)

    assert cleaned.equals(raw)
    review_log = next(
        entry for entry in log if entry["action"] == "review_ambiguous_date_format"
    )
    assert review_log["status"] == "needs_review"


def test_explicit_dayfirst_policy_allows_ambiguous_date_conversion():
    raw = pd.DataFrame({"event_date": ["01/02/2025", "02/03/2025"]})
    from app.preprocessing.raw_rule_engine import generate_preprocessing_plan
    from app.profiling.raw_profiler import profile_raw_dataframe

    plan = generate_preprocessing_plan(
        raw,
        profile_raw_dataframe(raw),
        date_dayfirst=True,
    )
    assert [action.action for action in plan.actions] == ["convert_to_datetime"]

    cleaned, _ = execute_preprocessing_plan(raw, plan, date_dayfirst=True)
    assert cleaned["event_date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2025-02-01",
        "2025-03-02",
    ]


def test_mixed_timezone_dates_are_normalized_to_utc():
    raw = pd.DataFrame(
        {
            "created_at": [
                "2025-01-01T00:00:00+00:00",
                "2025-01-02T00:00:00+05:30",
            ]
        }
    )
    plan = make_plan(
        PreprocessingAction(
            columns=["created_at"],
            action="convert_to_datetime",
            confidence=0.95,
            reason="timezone test",
        )
    )

    cleaned, log = execute_preprocessing_plan(raw, plan)

    assert str(cleaned["created_at"].dtype) == "datetime64[ns, UTC]"
    assert next(entry for entry in log if entry["action"] == "convert_to_datetime")[
        "timezone_policy"
    ] == "utc"


def test_boolean_conversion_rejects_unknown_non_null_values():
    raw = pd.DataFrame({"active": ["yes", "no", "maybe"]})
    plan = make_plan(
        PreprocessingAction(
            columns=["active"],
            action="convert_to_boolean",
            confidence=0.95,
            reason="boolean test",
        )
    )

    cleaned, log = execute_preprocessing_plan(raw, plan)

    assert cleaned["active"].tolist() == ["yes", "no", "maybe"]
    conversion_log = next(entry for entry in log if entry["action"] == "convert_to_boolean")
    assert conversion_log["status"] == "rejected"
    assert conversion_log["invalid_non_null_count"] == 1


def test_all_null_conversion_is_skipped_cleanly():
    raw = pd.DataFrame({"amount": [None, None]})
    plan = make_plan(
        PreprocessingAction(
            columns=["amount"],
            action="convert_to_numeric",
            confidence=0.95,
            reason="all-null test",
        )
    )

    cleaned, log = execute_preprocessing_plan(raw, plan)

    assert cleaned["amount"].isna().all()
    conversion_log = next(entry for entry in log if entry["action"] == "convert_to_numeric")
    assert conversion_log["status"] == "skipped"
    assert "entirely null" in conversion_log["reason"]


def test_unknown_action_is_distinguished_from_deliberate_review_skip():
    raw = pd.DataFrame({"value": [1, 2]})
    plan = make_plan(
        PreprocessingAction(
            columns=["value"], action="future_action", confidence=1.0, reason="unknown test"
        ),
        PreprocessingAction(
            columns=["value"], action="review_outliers", confidence=1.0, reason="review test"
        ),
    )

    cleaned, log = execute_preprocessing_plan(raw, plan)

    assert cleaned.equals(raw)
    assert next(entry for entry in log if entry["action"] == "future_action")["status"] == "unsupported"
    assert next(entry for entry in log if entry["action"] == "review_outliers")["status"] == "needs_review"

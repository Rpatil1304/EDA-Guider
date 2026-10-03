"""
Top-level orchestrator for the ingestion through reporting stage.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.execution.validator import Validator
from app.ingestion.loader import load_file
from app.preprocessing.preprocessor import execute_preprocessing_plan
from app.preprocessing.summary import build_preprocessing_summary_report
from app.schemas.preprocessing import PreprocessingPlan
from app.statistics.statistical_profiler import build_statistical_profile

from app.visualization.recommender import (
    generate_visualization_recommendations,
)

from app.visualization.evidence import (
    build_visualization_evidence,
)

from app.visualization.evidence_grouper import (
    group_visualization_evidence,
)

from app.langchain.model import (
    validate_visualization_recommendations,
    generate_final_report,
)

from app.langchain.report_evidence import (
    build_eda_report_evidence,
)


def _initial_result() -> dict[str, Any]:
    return {
        "status": "error",

        # ============================================================
        # Ingestion / profiling
        # ============================================================

        "ingestion_report": None,
        "raw_ydata_profile_report": None,
        "cleaned_ydata_profile_report": None,
        "structural_report": None,
        "raw_profile_report": None,

        # ============================================================
        # Preprocessing
        # ============================================================

        "preprocessing_plan": None,
        "execution_log": None,
        "preprocessing_summary_report": None,

        # ============================================================
        # Statistical analysis
        # ============================================================

        "statistical_profile": None,

        # ============================================================
        # Visualization
        # ============================================================

        "visualization_recommendations": None,
        "visualization_evidence": None,
        "visualization_evidence_groups": None,

        # ============================================================
        # LLM visualization validation
        # ============================================================

        "llm_visualization_validation": None,

        # ============================================================
        # Final report evidence
        # ============================================================

        "eda_report_evidence": None,

        "final_eda_report": None,

        # ============================================================
        # Internal data
        # ============================================================

        "cleaned_dataframe": None,

        # ============================================================
        # Error information
        # ============================================================

        "pipeline_error": None,
    }


def _failure(
    result: dict[str, Any],
    stage: str,
    error: Exception,
) -> dict[str, Any]:
    result["pipeline_error"] = {
        "stage": stage,
        "type": type(error).__name__,
        "message": str(error),
    }

    return result


def _save_cleaned_dataset_for_debug(
    cleaned_dataframe: pd.DataFrame,
    source,
) -> None:
    """Save the cleaned dataset locally for development/debugging only."""

    source_name = getattr(source, "name", None)

    if source_name:
        dataset_stem = Path(source_name).stem
    else:
        dataset_stem = "dataset"

    debug_directory = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "debug"
    )

    debug_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        debug_directory
        / f"{dataset_stem}_cleaned.csv"
    )

    cleaned_dataframe.to_csv(
        output_path,
        index=False,
    )

def _build_preprocessing_report_information(
    preprocessing_summary_report: dict[str, Any],
) -> dict[str, Any]:
    """Prepare preprocessing information for final report evidence."""

    summary = preprocessing_summary_report.get(
        "summary",
        {},
    )

    execution_log = preprocessing_summary_report.get(
        "execution_log",
        [],
    )

    steps = []

    for entry in execution_log:
        status = entry.get("status", "unknown")

        action = (
            entry.get("action")
            or entry.get("operation")
            or entry.get("rule")
            or entry.get("type")
        )

        columns = entry.get(
            "columns",
            [],
        )

        if action:
            if columns:
                steps.append(
                    f"{action} on columns: "
                    f"{', '.join(map(str, columns))} "
                    f"(status: {status})"
                )
            else:
                steps.append(
                    f"{action} "
                    f"(status: {status})"
                )
        else:
            steps.append(
                f"Preprocessing action "
                f"(status: {status})"
            )

    return {
        "steps": steps,
        "conversion_evidence": [
            {
                key: entry.get(key)
                for key in (
                    "columns",
                    "action",
                    "status",
                    "confidence",
                    "invalid_non_null_count",
                    "null_percentage_before",
                    "null_percentage_after",
                    "data_loss",
                    "timezone_policy",
                )
                if key in entry
            }
            for entry in execution_log
            if entry.get("action", "").startswith("convert_to_")
        ],
        "rows_before": summary.get(
            "raw_row_count",
            0,
        ),
        "rows_after": summary.get(
            "cleaned_row_count",
            0,
        ),
        "columns_before": summary.get(
            "raw_column_count",
            0,
        ),
        "columns_after": summary.get(
            "cleaned_column_count",
            0,
        ),
    }


def _generate_ydata_profile(
    dataframe: pd.DataFrame,
    source,
    dataset_label: str,
) -> dict[str, Any]:
    """Generate a YData HTML report for one pipeline dataset state."""

    output_path = None

    if isinstance(source, (str, Path)):
        source_path = Path(source)

        output_path = source_path.with_name(
            f"{source_path.stem}_{dataset_label}_profiling_report.html"
        )

    try:
        from ydata_profiling import ProfileReport

    except ImportError as error:
        return {
            "status": "unavailable",
            "output_path": (
                str(output_path)
                if output_path
                else None
            ),
            "error": (
                "ydata-profiling is not installed: "
                f"{error}"
            ),
        }

    profile = ProfileReport(
        dataframe.copy(deep=True),
        title=(
            f"EDA-Guider "
            f"{dataset_label.title()} Data Profile"
        ),
        minimal=True,
    )

    if output_path is None:
        return {
            "status": "generated_in_memory",
            "output_path": None,
            "html": profile.to_html(),
        }

    profile.to_file(output_path)

    return {
        "status": "generated",
        "output_path": str(output_path),
        "rows": len(dataframe),
        "columns": len(dataframe.columns),
    }


def run_preprocessing_pipeline(
    file_path_or_buffer,
    data_loss_threshold: float = 0.30,
    case_strategy: str = "lower",
    date_dayfirst: bool | None = None,
) -> dict[str, Any]:
    """
    Run the complete EDA-Guider pipeline.

    The pipeline performs:

    1. Data ingestion
    2. Structural validation
    3. Raw profiling
    4. Preprocessing planning
    5. Preprocessing execution
    6. Preprocessing summary
    7. Statistical profiling
    8. Rule-based visualization recommendation
    9. Visualization evidence generation
    10. Visualization evidence grouping
    11. LLM visualization validation
    12. Final EDA report evidence construction

    The original dataset is never modified.

    The cleaned dataframe is retained internally for downstream
    deterministic analysis and should not be exposed directly
    through an API response.
    """

    result = _initial_result()

    # ================================================================
    # Parts 1-4:
    # Ingestion, structural validation, raw profile,
    # preprocessing plan
    # ================================================================

    try:
        dataframe, ingestion_report = load_file(
            file_path_or_buffer,
            date_dayfirst=date_dayfirst,
        )

    except Exception as error:
        return _failure(
            result,
            "ingestion",
            error,
        )

    result["ingestion_report"] = ingestion_report

    result["structural_report"] = (
        ingestion_report.get("structural")
    )

    result["raw_profile_report"] = (
        ingestion_report.get("raw_profile")
    )

    result["preprocessing_plan"] = (
        ingestion_report.get("preprocessing_plan")
    )

    raw_snapshot = (
        dataframe.copy(deep=True)
        if dataframe is not None
        else None
    )

    if (
        dataframe is None
        or ingestion_report.get("status") != "success"
    ):
        error = ingestion_report.get("errors") or [
            {
                "type": "IngestionError",
                "message": "Ingestion failed.",
            }
        ]

        result["pipeline_error"] = {
            "stage": "ingestion",
            **error[0],
        }

        return result

    # ================================================================
    # Generate raw YData profile before preprocessing.
    # ================================================================

    try:
        result["raw_ydata_profile_report"] = (
            _generate_ydata_profile(
                dataframe,
                file_path_or_buffer,
                "raw",
            )
        )

    except Exception as error:
        result["raw_ydata_profile_report"] = {
            "status": "error",
            "output_path": None,
            "error": str(error),
        }

    if result["structural_report"] is None:
        return _failure(
            result,
            "structural_validation",
            ValueError(
                "The ingestion report did not contain "
                "a structural report."
            ),
        )

    if result["raw_profile_report"] is None:
        return _failure(
            result,
            "raw_profiling",
            ValueError(
                "The ingestion report did not contain "
                "a raw profile report."
            ),
        )

    if result["preprocessing_plan"] is None:
        return _failure(
            result,
            "preprocessing_planning",
            ValueError(
                "The ingestion report did not contain "
                "a preprocessing plan."
            ),
        )

    # ================================================================
    # Part 5:
    # Execute preprocessing plan.
    # ================================================================

    try:
        plan = PreprocessingPlan.model_validate(
            result["preprocessing_plan"]
        )

        cleaned_dataframe, execution_log = (
            execute_preprocessing_plan(
                dataframe,
                plan,
                data_loss_threshold=data_loss_threshold,
                case_strategy=case_strategy,
                date_dayfirst=date_dayfirst,
            )
        )

        result["execution_log"] = execution_log

        result["cleaned_dataframe"] = cleaned_dataframe

        source_unchanged = (
            raw_snapshot is not None
            and dataframe.equals(raw_snapshot)
        )

        validation = Validator.compare(
            dataframe,
            cleaned_dataframe,
        )

        if not validation["valid"]:
            return _failure(
                result,
                "preprocessing_validation",
                ValueError(
                    " ".join(validation["errors"])
                ),
            )

        _save_cleaned_dataset_for_debug(
            cleaned_dataframe,
            file_path_or_buffer,
        )

        try:
            result["cleaned_ydata_profile_report"] = (
                _generate_ydata_profile(
                    cleaned_dataframe,
                    file_path_or_buffer,
                    "cleaned",
                )
            )

        except Exception as error:
            result["cleaned_ydata_profile_report"] = {
                "status": "error",
                "output_path": None,
                "error": str(error),
            }

    except Exception as error:
        return _failure(
            result,
            "preprocessing_execution",
            error,
        )

    # ================================================================
    # Part 6:
    # Build preprocessing summary.
    # ================================================================

    try:
        result["preprocessing_summary_report"] = (
            build_preprocessing_summary_report(
                result["raw_profile_report"],
                result["cleaned_dataframe"],
                result["execution_log"],
            )
        )

        result["preprocessing_summary_report"][
            "raw_snapshot_unchanged"
        ] = source_unchanged

    except Exception as error:
        return _failure(
            result,
            "post_cleaning_summary",
            error,
        )

    # ================================================================
    # Part 7:
    # Calculate deterministic statistical evidence.
    # ================================================================

    try:
        result["statistical_profile"] = (
            build_statistical_profile(
                result["cleaned_dataframe"],
                result["preprocessing_summary_report"],
            )
        )

    except Exception as error:
        return _failure(
            result,
            "statistical_profiling",
            error,
        )

    # ================================================================
    # Part 8:
    # Generate deterministic visualization recommendations.
    # ================================================================

    try:
        result["visualization_recommendations"] = (
            generate_visualization_recommendations(
                result["statistical_profile"]
            )
        )

    except Exception as error:
        return _failure(
            result,
            "visualization_recommendation",
            error,
        )

    # ================================================================
    # Part 9:
    # Build structured visualization evidence.
    # ================================================================

    try:
        result["visualization_evidence"] = (
            build_visualization_evidence(
                result["statistical_profile"],
                result["visualization_recommendations"],
            )
        )

    except Exception as error:
        return _failure(
            result,
            "visualization_evidence",
            error,
        )

    # ================================================================
    # Part 10:
    # Group visualization evidence.
    # ================================================================

    try:
        result["visualization_evidence_groups"] = (
            group_visualization_evidence(
                result["visualization_evidence"]
            )
        )

    except Exception as error:
        return _failure(
            result,
            "visualization_evidence_grouping",
            error,
        )

    # ================================================================
    # Part 11:
    # LLM validates deterministic visualization recommendations.
    # ================================================================

        # ================================================================
    # Part 11:
    # Gemini #1 selects the best visualization recommendations.
    # ================================================================

    try:
        statistical_profile_data = (
            result["statistical_profile"].model_dump()
        )

        visualization_recommendation_data = (
            result[
                "visualization_recommendations"
            ].model_dump().get(
                "recommendations",
                [],
            )
        )

        result["llm_visualization_validation"] = (
            validate_visualization_recommendations(
                raw_profile_report=result["raw_profile_report"],
                preprocessing_summary_report=(
                    result["preprocessing_summary_report"]
                ),
                statistical_profile=statistical_profile_data,
                visualization_recommendations=(
                    visualization_recommendation_data
                ),
            )
        )

    except Exception as error:
        return _failure(
            result,
            "llm_visualization_validation",
            error,
        )

    # ================================================================
    # Part 12:
    # Build final privacy-safe EDA report evidence.
    # ================================================================

    try:
        statistical_profile_data = (
            result["statistical_profile"].model_dump()
        )

        validation_data = (
            result[
                "llm_visualization_validation"
            ].model_dump()
        )

        preprocessing_information = (
            _build_preprocessing_report_information(
                result[
                    "preprocessing_summary_report"
                ]
            )
        )

        result["eda_report_evidence"] = (
            build_eda_report_evidence(
                statistical_profile=(
                    statistical_profile_data
                ),
                preprocessing_information=(
                    preprocessing_information
                ),
                validation_response=(
                    validation_data
                ),
            )
        )

        # Generate final human-readable report
        result["final_eda_report"] = (
            generate_final_report(result)
        )

    except Exception as error:
        return _failure(
            result,
            "final_eda_report",
            error,
        )

    # ================================================================
    # Pipeline completed successfully.
    # ================================================================

    result["status"] = "success"

    return result

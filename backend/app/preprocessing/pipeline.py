"""Top-level orchestrator for the ingestion through preprocessing stage."""

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
from app.langchain.schemas import (
    LLMVisualizationRecommendation,
    LLMVisualizationResponse,
)

from app.langchain.model import (
    generate_llm_visualization_recommendations,
)


def _initial_result() -> dict[str, Any]:
    return {
        "status": "error",
        "ingestion_report": None,
        "raw_ydata_profile_report": None,
        "cleaned_ydata_profile_report": None,
        "structural_report": None,
        "raw_profile_report": None,
        "preprocessing_plan": None,
        "execution_log": None,
        "preprocessing_summary_report": None,
        "statistical_profile": None,
        "visualization_recommendations": None,
        "visualization_evidence": None,
        "visualization_evidence_groups": None,
        "llm_visualization_recommendations": None,
        "cleaned_dataframe": None,
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
            "output_path": str(output_path) if output_path else None,
            "error": f"ydata-profiling is not installed: {error}",
        }

    profile = ProfileReport(
        dataframe.copy(deep=True),
        title=f"EDA-Guider {dataset_label.title()} Data Profile",
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
) -> dict[str, Any]:
    """Run Parts 1 through 10 and return one structured pipeline result.

    This function never raises ordinary pipeline failures to its caller. A
    failed stage stops subsequent processing and leaves all reports created by
    earlier stages available in the returned object. ``cleaned_dataframe`` is
    included for the next internal pipeline stage and should not be exposed
    directly by an API response.
    """

    result = _initial_result()

    # ================================================================
    # Parts 1-4: ingestion, structural validation, raw profile, plan.
    # ================================================================
    try:
        dataframe, ingestion_report = load_file(
            file_path_or_buffer
        )

    except Exception as error:
        return _failure(
            result,
            "ingestion",
            error,
        )

    result["ingestion_report"] = ingestion_report
    result["structural_report"] = ingestion_report.get(
        "structural"
    )
    result["raw_profile_report"] = ingestion_report.get(
        "raw_profile"
    )
    result["preprocessing_plan"] = ingestion_report.get(
        "preprocessing_plan"
    )

    raw_snapshot = (
        dataframe.copy(deep=True)
        if dataframe is not None
        else None
    )

    if dataframe is None or ingestion_report.get("status") != "success":
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
    # Part 5: execute preprocessing plan.
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
    # Part 6: profile cleaned data and build final summary artifact.
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
    # Part 7: calculate deterministic statistical evidence.
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
    # Part 8: generate deterministic visualization
    # recommendations.
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
    # Part 9: build structured visualization evidence.
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
    # Part 10: group visualization evidence.
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
    # Pipeline completed successfully.
    # ================================================================
    result["status"] = "success"

    return result
"""Build privacy-safe evidence for final EDA report generation."""

from __future__ import annotations

from typing import Any

from app.langchain.report_schemas import (
    ConversionEvidence,
    DatasetReportEvidence,
    EDAReportEvidence,
    PreprocessingReportEvidence,
    StatisticalReportEvidence,
    VisualizationReportEvidence,
)


# ================================================================
# Dataset Evidence
# ================================================================

def build_dataset_report_evidence(
    statistical_profile: dict[str, Any],
) -> DatasetReportEvidence:
    """Build dataset-level evidence from the statistical profile."""

    columns = statistical_profile.get(
        "columns",
        {},
    )

    numeric_columns = []
    categorical_columns = []
    datetime_columns = []
    boolean_columns = []
    missing_value_columns = []

    for column_name, column_data in columns.items():

        inferred_type = column_data.get(
            "inferred_type"
        )

        if inferred_type == "numeric":
            numeric_columns.append(column_name)

        elif inferred_type == "categorical":
            categorical_columns.append(column_name)

        elif inferred_type == "datetime":
            datetime_columns.append(column_name)

        elif inferred_type == "boolean":
            boolean_columns.append(column_name)

        if column_data.get(
            "missing_count",
            0,
        ) > 0:
            missing_value_columns.append(
                column_name
            )

    return DatasetReportEvidence(
        row_count=statistical_profile.get(
            "n_rows",
            0,
        ),
        column_count=statistical_profile.get(
            "n_cols",
            0,
        ),
        numeric_columns=numeric_columns,
        categorical_columns=categorical_columns,
        datetime_columns=datetime_columns,
        boolean_columns=boolean_columns,
        missing_value_columns=missing_value_columns,
    )


# ================================================================
# Preprocessing Evidence
# ================================================================

def build_preprocessing_report_evidence(
    preprocessing_information: dict[str, Any],
) -> PreprocessingReportEvidence:
    """Build evidence describing preprocessing operations."""

    return PreprocessingReportEvidence(
        steps=preprocessing_information.get(
            "steps",
            [],
        ),
        rows_before=preprocessing_information.get(
            "rows_before",
            0,
        ),
        rows_after=preprocessing_information.get(
            "rows_after",
            0,
        ),
        columns_before=preprocessing_information.get(
            "columns_before",
            0,
        ),
        columns_after=preprocessing_information.get(
            "columns_after",
            0,
        ),
        conversion_evidence=[
            ConversionEvidence.model_validate(item)
            for item in preprocessing_information.get(
                "conversion_evidence",
                [],
            )
        ],
    )


# ================================================================
# Statistical Evidence
# ================================================================

def build_statistical_report_evidence(
    statistical_profile: dict[str, Any],
) -> StatisticalReportEvidence:
    """Build privacy-safe statistical evidence."""

    return StatisticalReportEvidence(
        numeric_statistics=statistical_profile.get(
            "numeric_columns",
            {},
        ),
        categorical_statistics=statistical_profile.get(
            "categorical_columns",
            {},
        ),
        datetime_statistics=statistical_profile.get(
            "datetime_columns",
            {},
        ),
        boolean_statistics=statistical_profile.get(
            "boolean_columns",
            {},
        ),
        correlation_matrix=statistical_profile.get(
            "correlation_matrix",
            {},
        ),
    )


# ================================================================
# Visualization Evidence
# ================================================================

def build_visualization_report_evidence(
    validation_response: dict[str, Any],
) -> VisualizationReportEvidence:
    """Build final visualization evidence from LLM validation."""

    accepted = []
    modified = []
    rejected = []

    validations = validation_response.get(
        "validations",
        [],
    )

    for validation in validations:

        decision = validation.get(
            "decision"
        )

        item = {
            "original_chart_type": validation.get(
                "original_chart_type"
            ),
            "original_columns": validation.get(
                "original_columns",
                [],
            ),
            "final_chart_type": validation.get(
                "final_chart_type"
            ),
            "final_columns": validation.get(
                "final_columns",
                [],
            ),
            "reason": validation.get(
                "reason",
                "",
            ),
            "confidence": validation.get(
                "confidence",
                0.0,
            ),
        }

        if decision == "accepted":
            accepted.append(item)

        elif decision == "modified":
            modified.append(item)

        elif decision == "rejected":
            rejected.append(item)

    return VisualizationReportEvidence(
        accepted=accepted,
        modified=modified,
        rejected=rejected,
    )


# ================================================================
# Complete Report Evidence
# ================================================================

def build_eda_report_evidence(
    statistical_profile: dict[str, Any],
    preprocessing_information: dict[str, Any],
    validation_response: dict[str, Any],
) -> EDAReportEvidence:
    """
    Build the complete privacy-safe evidence object for
    final EDA report generation.
    """

    dataset_evidence = build_dataset_report_evidence(
        statistical_profile
    )

    preprocessing_evidence = (
        build_preprocessing_report_evidence(
            preprocessing_information
        )
    )

    statistical_evidence = (
        build_statistical_report_evidence(
            statistical_profile
        )
    )

    visualization_evidence = (
        build_visualization_report_evidence(
            validation_response
        )
    )

    return EDAReportEvidence(
        dataset=dataset_evidence,
        preprocessing=preprocessing_evidence,
        statistics=statistical_evidence,
        visualizations=visualization_evidence,
    )
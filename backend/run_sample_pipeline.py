"""Run the implemented EDA-Guider stages against one local CSV or Excel file.

Edit CSV_PATH below, then run from the backend directory:

    python run_sample_pipeline.py
"""

from __future__ import annotations

from pathlib import Path

from app.preprocessing.pipeline import run_preprocessing_pipeline
from app.reporting import generate_eda_guide_report


# Edit this path. Absolute paths and paths relative to the backend directory work.
CSV_PATH = Path(
    r"C:\Users\rohit\OneDrive\Documents\Project\EDA-Guider"
    r"\Datasets\Raw\eda_guider_100_rows_messy_sample.csv"
)


def print_section(title: str) -> None:
    print(f"\n{'=' * 20} {title} {'=' * 20}")


def main() -> None:

    if (
        "your" in str(CSV_PATH).lower()
        or not CSV_PATH.exists()
    ):
        print(
            "Update CSV_PATH in run_sample_pipeline.py "
            "to point to your file."
        )
        print(
            f"Current path: {CSV_PATH}"
        )
        return

    # ------------------------------------------------------------------
    # Run the complete pipeline.
    # ------------------------------------------------------------------

    result = run_preprocessing_pipeline(
        CSV_PATH
    )

    # ------------------------------------------------------------------
    # Pipeline status
    # ------------------------------------------------------------------

    print_section(
        "PIPELINE STATUS"
    )

    print(
        result["status"]
    )

    # ------------------------------------------------------------------
    # Pipeline error
    # ------------------------------------------------------------------

    if result["pipeline_error"]:

        print_section(
            "PIPELINE ERROR"
        )

        print(
            result["pipeline_error"]
        )

    # ------------------------------------------------------------------
    # YData raw profile
    # ------------------------------------------------------------------

    print_section(
        "RAW YDATA PROFILING REPORT"
    )

    print(
        result.get(
            "raw_ydata_profile_report"
        )
    )

    # ------------------------------------------------------------------
    # YData cleaned profile
    # ------------------------------------------------------------------

    print_section(
        "CLEANED YDATA PROFILING REPORT"
    )

    print(
        result.get(
            "cleaned_ydata_profile_report"
        )
    )

    # ------------------------------------------------------------------
    # Parts 1-2
    # ------------------------------------------------------------------

    ingestion = result[
        "ingestion_report"
    ]

    if ingestion:

        print_section(
            "PARTS 1-2: INGESTION AND STRUCTURE"
        )

        print({
            "status": ingestion.get("status"),
            "file_name": ingestion.get("file_name"),
            "file_type": ingestion.get("file_type"),
            "encoding": ingestion.get("encoding"),
            "delimiter": ingestion.get("delimiter"),
            "header_present": ingestion.get("header_present"),
            "rows": ingestion.get("rows"),
            "columns": ingestion.get("columns"),
            "warnings": ingestion.get("warnings"),
            "errors": ingestion.get("errors"),
        })

        print(
            "\nStructural report:"
        )

        print(
            result[
                "structural_report"
            ]
        )

    # ------------------------------------------------------------------
    # Part 3
    # ------------------------------------------------------------------

    raw_profile = result[
        "raw_profile_report"
    ]

    if raw_profile:

        print_section(
            "PART 3: RAW PROFILE"
        )

        print({
            "rows": raw_profile.get(
                "row_count"
            ),
            "columns": raw_profile.get(
                "column_count"
            ),
            "warning_count": len(
                raw_profile.get(
                    "warnings",
                    [],
                )
            ),
        })

        for column in raw_profile.get(
            "columns",
            [],
        ):

            print({
                "column": column.get("name"),
                "dtype": column.get("dtype"),
                "semantic_type": column.get(
                    "semantic_type"
                ),
                "null_percentage": column.get(
                    "null_percentage"
                ),
                "unique_count": column.get(
                    "unique_count"
                ),
            })

        print(
            "\nNull-value summary:"
        )

        print(
            raw_profile.get(
                "null_summary",
                {},
            )
        )

        for column in raw_profile.get(
            "columns",
            [],
        ):

            if (
                column.get("null_count")
                or column.get("null_like_count")
            ):

                print({
                    "column": column.get(
                        "name"
                    ),
                    "actual_null_count": column.get(
                        "null_count"
                    ),
                    "actual_null_percentage": column.get(
                        "null_percentage"
                    ),
                    "null_like_count": column.get(
                        "null_like_count"
                    ),
                    "null_like_breakdown": column.get(
                        "null_like_breakdown"
                    ),
                })

        if raw_profile.get(
            "warnings"
        ):

            print(
                "\nRaw-profile warnings:"
            )

            for warning in raw_profile[
                "warnings"
            ]:
                print(
                    warning
                )

    # ------------------------------------------------------------------
    # Part 4
    # ------------------------------------------------------------------

    plan = result[
        "preprocessing_plan"
    ]

    if plan:

        print_section(
            "PART 4: PREPROCESSING PLAN"
        )

        for action in plan.get(
            "actions",
            [],
        ):

            print({
                "columns": action.get(
                    "columns"
                ),
                "action": action.get(
                    "action"
                ),
                "confidence": action.get(
                    "confidence"
                ),
                "reason": action.get(
                    "reason"
                ),
            })

    # ------------------------------------------------------------------
    # Part 5
    # ------------------------------------------------------------------

    if result[
        "execution_log"
    ] is not None:

        print_section(
            "PART 5: EXECUTION LOG"
        )

        for entry in result[
            "execution_log"
        ]:

            print(
                entry
            )

    # ------------------------------------------------------------------
    # Part 6
    # ------------------------------------------------------------------

    summary = result[
        "preprocessing_summary_report"
    ]

    if summary:

        print_section(
            "PART 6: PREPROCESSING SUMMARY"
        )

        print(
            summary.get(
                "summary"
            )
        )

        print(
            "\nDownstream handoff:"
        )

        print(
            summary.get(
                "downstream_handoff"
            )
        )

        for column in summary.get(
            "columns",
            [],
        ):

            print({
                "before": column.get(
                    "column_before"
                ),
                "after": column.get(
                    "column_after"
                ),
                "changes": column.get(
                    "changes"
                ),
                "action_count": len(
                    column.get(
                        "actions",
                        [],
                    )
                ),
            })

    # ------------------------------------------------------------------
    # Part 7 - Statistical profile
    # ------------------------------------------------------------------

    statistical_profile = result.get(
        "statistical_profile"
    )

    if statistical_profile is not None:
        statistical_profile = statistical_profile.model_dump()

    if statistical_profile:

        print_section(
            "PART 7: STATISTICAL PROFILE"
        )

        print(
            "Dataset:"
        )

        print({
            "rows": statistical_profile.get(
                "n_rows"
            ),
            "columns": statistical_profile.get(
                "n_cols"
            ),
        })

        # --------------------------------------------------------------
        # Eligible column overview
        # --------------------------------------------------------------

        print(
            "\nEligible columns:"
        )

        for column, stats in (
            statistical_profile.get(
                "columns",
                {}
            ).items()
        ):

            print({
                "column": column,
                "inferred_type": stats.get(
                    "inferred_type"
                ),
                "count": stats.get(
                    "count"
                ),
                "missing_count": stats.get(
                    "missing_count"
                ),
                "missing_percentage": stats.get(
                    "missing_percentage"
                ),
                "unique_count": stats.get(
                    "unique_count"
                ),
            })

        # --------------------------------------------------------------
        # Numeric
        # --------------------------------------------------------------

        print(
            "\nNumeric statistics:"
        )

        for column, stats in (
            statistical_profile.get(
                "numeric_columns",
                {}
            ).items()
        ):

            print({
                "column": column,
                "count": stats.get("count"),
                "mean": stats.get("mean"),
                "median": stats.get("median"),
                "std": stats.get("std"),
                "minimum": stats.get("minimum"),
                "maximum": stats.get("maximum"),
                "q1": stats.get("q1"),
                "q3": stats.get("q3"),
                "skewness": stats.get("skewness"),
                "kurtosis": stats.get("kurtosis"),
                "iqr": stats.get("iqr"),
                "lower_bound": stats.get(
                    "lower_bound"
                ),
                "upper_bound": stats.get(
                    "upper_bound"
                ),
                "outlier_count": stats.get(
                    "outlier_count"
                ),
                "outlier_percentage": stats.get(
                    "outlier_percentage"
                ),
            })

        # --------------------------------------------------------------
        # Categorical
        # --------------------------------------------------------------

        print(
            "\nCategorical statistics:"
        )

        for column, stats in (
            statistical_profile.get(
                "categorical_columns",
                {}
            ).items()
        ):

            print({
                "column": column,
                "count": stats.get(
                    "count"
                ),
                "unique_count": stats.get(
                    "unique_count"
                ),
                "top": stats.get(
                    "top"
                ),
                "top_frequency": stats.get(
                    "top_frequency"
                ),
                "top_percentage": stats.get(
                    "top_percentage"
                ),
                "top_categories": stats.get(
                    "top_categories"
                ),
            })

        # --------------------------------------------------------------
        # Datetime
        # --------------------------------------------------------------

        print(
            "\nDatetime statistics:"
        )

        for column, stats in (
            statistical_profile.get(
                "datetime_columns",
                {}
            ).items()
        ):

            print({
                "column": column,
                "count": stats.get(
                    "count"
                ),
                "minimum": stats.get(
                    "minimum"
                ),
                "maximum": stats.get(
                    "maximum"
                ),
                "unique_count": stats.get(
                    "unique_count"
                ),
                "duration_days": stats.get(
                    "duration_days"
                ),
            })

        # --------------------------------------------------------------
        # Boolean
        # --------------------------------------------------------------

        print(
            "\nBoolean statistics:"
        )

        for column, stats in (
            statistical_profile.get(
                "boolean_columns",
                {}
            ).items()
        ):

            print({
                "column": column,
                "count": stats.get(
                    "count"
                ),
                "true_count": stats.get(
                    "true_count"
                ),
                "true_percentage": stats.get(
                    "true_percentage"
                ),
                "false_count": stats.get(
                    "false_count"
                ),
                "false_percentage": stats.get(
                    "false_percentage"
                ),
            })

        # --------------------------------------------------------------
        # Correlation
        # --------------------------------------------------------------

        print(
            "\nCorrelation matrix:"
        )

        print(
            statistical_profile.get(
                "correlation_matrix",
                {}
            )
        )

    else:

        print_section(
            "PART 7: STATISTICAL PROFILE"
        )

        print(
            "Statistical profiling was not generated."
        )

    # ------------------------------------------------------------------
    # Part 8 - Visualization recommendations
    # ------------------------------------------------------------------

    visualization_recommendations = result.get(
        "visualization_recommendations"
    )

    if visualization_recommendations is not None:

        print_section(
            "PART 8: VISUALIZATION RECOMMENDATIONS"
        )

        for recommendation in (
            visualization_recommendations.recommendations
        ):

            print(
                f"\nChart Type : "
                f"{recommendation.chart_type}"
                f"\nColumns    : "
                f"{recommendation.columns}"
                f"\nReason     : "
                f"{recommendation.reason}"
                f"\nConfidence : "
                f"{recommendation.confidence}"
                f"\nPriority   : "
                f"{recommendation.priority}"
                f"\nRule ID    : "
                f"{recommendation.rule_id}"
            )

    # ------------------------------------------------------------------
    # Part 9 - Visualization evidence
    # ------------------------------------------------------------------

    visualization_evidence = result.get(
        "visualization_evidence"
    )

    if visualization_evidence is not None:

        print_section(
            "PART 9: VISUALIZATION EVIDENCE"
        )

        for evidence in visualization_evidence.evidence:

            print(
                f"\nChart Type : "
                f"{evidence.chart_type}"
                f"\nColumns    : "
                f"{evidence.columns}"
                f"\nRule ID    : "
                f"{evidence.rule_id}"
                f"\nConfidence : "
                f"{evidence.confidence}"
                f"\nPriority   : "
                f"{evidence.priority}"
                f"\nRow Count  : "
                f"{evidence.row_count}"
                f"\nStatistics : "
                f"{evidence.column_statistics}"
            )
    # ------------------------------------------------------------------
    # Part 10 - Grouped visualization evidence
    # ------------------------------------------------------------------

    visualization_evidence_groups = result.get(
        "visualization_evidence_groups"
    )

    if visualization_evidence_groups is not None:

        print_section(
            "PART 10: GROUPED VISUALIZATION EVIDENCE"
        )

        for rule_id, evidence_items in (
            visualization_evidence_groups.items()
        ):

            print(
                f"\nRule ID : {rule_id}"
            )

            print(
                f"Recommendation count : "
                f"{len(evidence_items)}"
            )

            for item in evidence_items:

                print(
                    f"  Chart Type : "
                    f"{item.get('chart_type')}"
                    f"\n  Columns    : "
                    f"{item.get('columns')}"
                    f"\n  Confidence : "
                    f"{item.get('confidence')}"
                )
    # ------------------------------------------------------------------
    # Part 11 - LLM visualization validation
    # ------------------------------------------------------------------

    llm_visualization_validation = result.get(
        "llm_visualization_validation"
    )

    if llm_visualization_validation is not None:

        print_section(
            "PART 11: LLM VISUALIZATION VALIDATION"
        )

        print(
            llm_visualization_validation.model_dump()
        )

    # ------------------------------------------------------------------
    # Part 12 - Final EDA report evidence
    # ------------------------------------------------------------------

    eda_report_evidence = result.get(
        "eda_report_evidence"
    )

    if eda_report_evidence is not None:

        print_section(
            "PART 12: FINAL EDA REPORT EVIDENCE"
        )

        print(
            eda_report_evidence.model_dump()
        )
    # ------------------------------------------------------------------
    # Save processed CSV + Markdown report
    # ------------------------------------------------------------------

    cleaned = result[
        "cleaned_dataframe"
    ]

    if cleaned is not None:

        processed_path = CSV_PATH.with_name(
            f"{CSV_PATH.stem}_processed.csv"
        )

        cleaned.to_csv(
            processed_path,
            index=False,
        )

        print_section(
            "PROCESSED CSV OUTPUT"
        )

        print(
            f"Saved processed data to: "
            f"{processed_path}"
        )

        print(
            "The original raw file was not modified."
        )

        print_section(
            "CLEANED DATAFRAME PREVIEW"
        )

        print(
            cleaned.head(10).to_string(
                index=False
            )
        )

        print(
            f"\nShape: {cleaned.shape[0]} rows "
            f"x {cleaned.shape[1]} columns"
        )

        # --------------------------------------------------------------
        # Generate Markdown report.
        # --------------------------------------------------------------

        report_path = CSV_PATH.with_name(
            f"{CSV_PATH.stem}_eda_report.md"
        )

        generate_eda_guide_report(
            result,
            report_path,
        )

        print_section(
            "EDA REPORT"
        )

        print(
            f"Saved step-by-step EDA report to: "
            f"{report_path}"
        )


if __name__ == "__main__":
    main()
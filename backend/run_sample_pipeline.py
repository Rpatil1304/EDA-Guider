"""Run Parts 1-7 of EDA-Guider against one local CSV or Excel file.

Edit CSV_PATH below, then run from the backend directory:

    python run_sample_pipeline.py
"""

from __future__ import annotations

from pathlib import Path

from app.preprocessing.pipeline import run_preprocessing_pipeline


# Edit this path. Absolute paths and paths relative to the backend directory work.
CSV_PATH = Path(r"C:\Users\rohit\OneDrive\Documents\Project\EDA-Guider\03_Calfus_Candidate_Delivery_Data.csv")


def print_section(title: str) -> None:
    print(f"\n{'=' * 20} {title} {'=' * 20}")


def main() -> None:
    if "your" in str(CSV_PATH).lower() or not CSV_PATH.exists():
        print("Update CSV_PATH in run_sample_pipeline.py to point to your file.")
        print(f"Current path: {CSV_PATH}")
        return

    result = run_preprocessing_pipeline(CSV_PATH)

    print_section("PIPELINE STATUS")
    print(result["status"])

    if result["pipeline_error"]:
        print_section("PIPELINE ERROR")
        print(result["pipeline_error"])

    ingestion = result["ingestion_report"]
    if ingestion:
        print_section("PARTS 1-2: INGESTION AND STRUCTURE")
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
        print("\nStructural report:")
        print(result["structural_report"])

    raw_profile = result["raw_profile_report"]
    if raw_profile:
        print_section("PART 3: RAW PROFILE")
        print({
            "rows": raw_profile.get("row_count"),
            "columns": raw_profile.get("column_count"),
            "warning_count": len(raw_profile.get("warnings", [])),
        })
        for column in raw_profile.get("columns", []):
            print({
                "column": column.get("name"),
                "dtype": column.get("dtype"),
                "null_percentage": column.get("null_percentage"),
                "unique_count": column.get("unique_count"),
                "sample_values": column.get("sample_values"),
            })
            print("\nNull-value summary:")
            print(raw_profile.get("null_summary", {}))
            for column in raw_profile.get("columns", []):
                if column.get("null_count") or column.get("null_like_count"):
                    print({
                        "column": column.get("name"),
                        "actual_null_count": column.get("null_count"),
                        "actual_null_percentage": column.get("null_percentage"),
                        "null_like_count": column.get("null_like_count"),
                        "null_like_breakdown": column.get("null_like_breakdown"),
                    })
        if raw_profile.get("warnings"):
            print("\nRaw-profile warnings:")
            for warning in raw_profile["warnings"]:
                print(warning)

    plan = result["preprocessing_plan"]
    if plan:
        print_section("PART 4: PREPROCESSING PLAN")
        for action in plan.get("actions", []):
            print({
                "columns": action.get("columns"),
                "action": action.get("action"),
                "confidence": action.get("confidence"),
                "reason": action.get("reason"),
            })

    if result["execution_log"] is not None:
        print_section("PART 5: EXECUTION LOG")
        for entry in result["execution_log"]:
            print(entry)

    summary = result["preprocessing_summary_report"]
    if summary:
        print_section("PART 6: PREPROCESSING SUMMARY")
        print(summary.get("summary"))
        for column in summary.get("columns", []):
            print({
                "before": column.get("column_before"),
                "after": column.get("column_after"),
                "changes": column.get("changes"),
                "action_count": len(column.get("actions", [])),
            })

    cleaned = result["cleaned_dataframe"]
    if cleaned is not None:
        processed_path = CSV_PATH.with_name(
            f"{CSV_PATH.stem}_processed.csv"
        )
        cleaned.to_csv(processed_path, index=False)

        print_section("PROCESSED CSV OUTPUT")
        print(f"Saved processed data to: {processed_path}")
        print("The original raw file was not modified.")

        print_section("CLEANED DATAFRAME PREVIEW")
        print(cleaned.head(10).to_string(index=False))
        print(f"\nShape: {cleaned.shape[0]} rows x {cleaned.shape[1]} columns")


if __name__ == "__main__":
    main()

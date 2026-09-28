
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.orchestration.pipeline import run_preprocessing_pipeline


app = FastAPI(
    title="EDA-Guider",
    version="1.0.0",
)


# ============================================================
# CORS configuration
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Health check
# ============================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""

    return {
        "status": "ok"
    }


# ============================================================
# Dataset analysis
# ============================================================

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    """
    Analyze an uploaded CSV or Excel dataset.

    The uploaded file is temporarily saved and passed
    to the existing EDA-Guider pipeline.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename was provided.",
        )

    file_extension = Path(file.filename).suffix.lower()

    supported_extensions = {
        ".csv",
        ".tsv",
        ".xlsx",
        ".xls",
        ".xlsm",
    }

    if file_extension not in supported_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file format. "
                "Supported formats are CSV, TSV, XLS, XLSX, and XLSM."
            ),
        )

    temporary_path = None

    try:
        # --------------------------------------------------------
        # Save uploaded file temporarily
        # --------------------------------------------------------

        file_content = await file.read()

        with NamedTemporaryFile(
            delete=False,
            suffix=file_extension,
        ) as temporary_file:

            temporary_file.write(file_content)
            temporary_path = Path(temporary_file.name)

        # --------------------------------------------------------
        # Run the existing EDA pipeline
        # --------------------------------------------------------

        result = run_preprocessing_pipeline(
            temporary_path
        )

        # --------------------------------------------------------
        # Check pipeline status
        # --------------------------------------------------------

        if result.get("status") != "success":

            pipeline_error = result.get(
                "pipeline_error"
            )

            print("\n================ PIPELINE ERROR ================")
            print(pipeline_error)
            print("=================================================\n")

            raise HTTPException(
                status_code=500,
                detail={
                    "message": "EDA pipeline failed.",
                    "error": pipeline_error,
                },
            )

        # --------------------------------------------------------
        # Return privacy-safe report information
        #
        # Do NOT return cleaned_dataframe.
        # --------------------------------------------------------

        return {
            "status": "success",
            "filename": file.filename,

            "ingestion": result.get(
                "ingestion_report"
            ),

            "raw_profile": result.get(
                "raw_profile_report"
            ),

            "preprocessing": result.get(
                "preprocessing_summary_report"
            ),

            "statistics": (
                result["statistical_profile"].model_dump()
                if result.get("statistical_profile")
                else None
            ),

            "visualization_recommendations": (
                result[
                    "visualization_recommendations"
                ].model_dump()
                if result.get(
                    "visualization_recommendations"
                )
                else None
            ),

            "visualization_evidence": (
                result[
                    "visualization_evidence"
                ].model_dump()
                if result.get(
                    "visualization_evidence"
                )
                else None
            ),

            "visualization_validation": (
                result[
                    "llm_visualization_validation"
                ].model_dump()
                if result.get(
                    "llm_visualization_validation"
                )
                else None
            ),

            "eda_report": result.get(
                "eda_report_evidence"
            ),

            "final_eda_report": (
                result["final_eda_report"].model_dump()
                if result.get("final_eda_report")
                else None
            ),
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to analyze the uploaded dataset.",
                "type": type(error).__name__,
                "error": str(error),
            },
        )

    finally:

        # --------------------------------------------------------
        # Delete temporary uploaded file
        # --------------------------------------------------------

        if temporary_path is not None:

            try:
                temporary_path.unlink(
                    missing_ok=True
                )
            except Exception:
                pass


"""FastAPI router for the Clean dataset Q&A and visualization endpoints."""

from __future__ import annotations

import json
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.clean_query.dataset_loader import load_clean_dataset
from app.clean_query.metadata_extractor import extract_dataset_metadata
from app.clean_query.service import process_clean_query

clean_router = APIRouter()


@clean_router.post("/metadata")
async def get_clean_metadata(
    file: UploadFile = File(...),
):
    """Upload a clean CSV or Excel dataset and return its schema and statistical metadata."""
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided in upload.",
        )

    try:
        content = await file.read()
        df = load_clean_dataset(content, filename=file.filename)
        metadata = extract_dataset_metadata(df)
        return {
            "status": "success",
            "filename": file.filename,
            "metadata": metadata,
        }
    except ValueError as val_err:
        raise HTTPException(
            status_code=400,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to extract metadata from clean dataset.",
                "error": str(exc),
            },
        )


@clean_router.post("/query")
async def query_clean_dataset_endpoint(
    file: UploadFile = File(...),
    query: str = Form(...),
    metadata_json: Optional[str] = Form(None),
):
    """Submit a natural language query against an uploaded clean CSV or Excel dataset.

    Executes metadata profiling, code generation, sandboxed execution,
    and returns a synthesized natural-language answer along with data/charts.
    """
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided in upload.",
        )

    if not query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty.",
        )

    try:
        content = await file.read()
        df = load_clean_dataset(content, filename=file.filename)

        metadata = None
        if metadata_json:
            try:
                metadata = json.loads(metadata_json)
            except Exception:
                metadata = None

        result = process_clean_query(
            df=df,
            user_query=query,
            metadata=metadata,
        )

        return result

    except ValueError as val_err:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=400,
            detail=str(val_err),
        )
    except Exception as exc:
        import traceback
        print("\n================ CLEAN QUERY ERROR ================")
        traceback.print_exc()
        print("===================================================\n")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to process query on clean dataset.",
                "error": str(exc),
            },
        )

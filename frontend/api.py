import json
from typing import Any, Dict, Optional
import requests

from config import (
    ANALYZE_ENDPOINT,
    CLEAN_METADATA_ENDPOINT,
    CLEAN_QUERY_ENDPOINT,
)


def analyze_dataset(file):
    """
    Send the uploaded dataset to the FastAPI backend
    and return the generated EDA report.
    """
    files = {
        "file": (
            file.name,
            file.getvalue(),
            file.type or "application/octet-stream",
        )
    }

    response = requests.post(
        ANALYZE_ENDPOINT,
        files=files,
        timeout=300,
    )

    response.raise_for_status()

    return response.json()


def fetch_clean_metadata(file) -> Dict[str, Any]:
    """Fetch structural and statistical metadata for a clean CSV/Excel dataset."""
    files = {
        "file": (
            file.name,
            file.getvalue(),
            file.type or "application/octet-stream",
        )
    }

    response = requests.post(
        CLEAN_METADATA_ENDPOINT,
        files=files,
        timeout=120,
    )

    response.raise_for_status()
    return response.json()


def submit_clean_query(
    file,
    query: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Submit a natural language query against the clean dataset."""
    files = {
        "file": (
            file.name,
            file.getvalue(),
            file.type or "application/octet-stream",
        )
    }

    data = {
        "query": query,
    }

    if metadata:
        data["metadata_json"] = json.dumps(metadata)

    response = requests.post(
        CLEAN_QUERY_ENDPOINT,
        files=files,
        data=data,
        timeout=180,
    )

    if not response.ok:
        try:
            err_data = response.json()
            err_detail = err_data.get("detail", err_data)
        except Exception:
            err_detail = response.text
        raise RuntimeError(f"Server Error ({response.status_code}): {err_detail}")

    return response.json()

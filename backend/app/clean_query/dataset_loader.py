"""Dataset loader for the Clean section.

Supports loading cleaned tabular datasets from CSV, TSV, and Excel (XLSX, XLS, XLSM)
sources, accepting file paths, byte streams, or uploaded file buffers.
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any, BinaryIO, Optional, Union

import pandas as pd


SupportedFile = Union[str, os.PathLike, BinaryIO, bytes]


def load_clean_dataset(
    file_source: SupportedFile,
    filename: Optional[str] = None,
    sheet_name: Optional[Union[str, int]] = 0,
) -> pd.DataFrame:
    """Load a clean dataset from a CSV, TSV, or Excel file/buffer.

    Parameters
    ----------
    file_source : Union[str, os.PathLike, BinaryIO, bytes]
        File path, file-like object (e.g. Streamlit UploadedFile), or raw bytes.
    filename : Optional[str]
        Explicit filename or extension hint if file_source does not have a `.name` attribute.
    sheet_name : Optional[Union[str, int]]
        For Excel files, the sheet to read (defaults to 0, the first sheet).

    Returns
    -------
    pd.DataFrame
        Loaded pandas DataFrame.

    Raises
    ------
    ValueError
        If the file format is unsupported, unreadable, or produces an empty DataFrame.
    """
    detected_name = filename
    raw_bytes: bytes

    # Extract bytes and filename
    if isinstance(file_source, (str, os.PathLike)):
        path = Path(file_source)
        if not path.is_file():
            raise ValueError(f"File not found: {path}")
        raw_bytes = path.read_bytes()
        if not detected_name:
            detected_name = path.name

    elif isinstance(file_source, bytes):
        raw_bytes = file_source

    elif hasattr(file_source, "read"):
        if not detected_name and hasattr(file_source, "name"):
            detected_name = str(file_source.name)
        
        # Seek to beginning if possible
        if hasattr(file_source, "seek"):
            try:
                file_source.seek(0)
            except Exception:
                pass
        
        content = file_source.read()
        if isinstance(content, str):
            raw_bytes = content.encode("utf-8")
        elif isinstance(content, bytes):
            raw_bytes = content
        else:
            raise ValueError("Unsupported content type from readable file source.")
    else:
        raise ValueError("Invalid file_source: expected path, bytes, or file-like object.")

    if not raw_bytes:
        raise ValueError("The uploaded file is empty (0 bytes).")

    # Detect extension
    extension = ""
    if detected_name:
        extension = Path(detected_name).suffix.lower().lstrip(".")

    # If extension is still missing, try to infer from magic bytes
    if not extension:
        if raw_bytes.startswith(b"PK\x03\x04"):
            extension = "xlsx"
        elif raw_bytes.startswith(b"\xd0\xcf\x11\xe0"):
            extension = "xls"
        else:
            extension = "csv"

    supported_extensions = {"csv", "tsv", "xlsx", "xls", "xlsm"}
    if extension not in supported_extensions:
        raise ValueError(
            f"Unsupported file format '.{extension}'. "
            "Supported formats are CSV, TSV, XLSX, XLS, and XLSM."
        )

    # Load based on format
    buffer = io.BytesIO(raw_bytes)

    if extension in {"xlsx", "xlsm"}:
        try:
            df = pd.read_excel(buffer, engine="openpyxl", sheet_name=sheet_name)
        except Exception as exc:
            raise ValueError(f"Failed to read Excel file (.xlsx/.xlsm): {exc}") from exc

    elif extension == "xls":
        try:
            df = pd.read_excel(buffer, engine="xlrd", sheet_name=sheet_name)
        except Exception as exc:
            raise ValueError(f"Failed to read Excel file (.xls): {exc}") from exc

    else:
        # CSV or TSV
        delimiter = "\t" if extension == "tsv" else None
        df = None
        encodings_to_try = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

        for enc in encodings_to_try:
            try:
                buffer.seek(0)
                if delimiter:
                    df = pd.read_csv(buffer, encoding=enc, sep=delimiter)
                else:
                    df = pd.read_csv(buffer, encoding=enc)
                break
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue

        if df is None:
            # Fallback using chardet if available
            try:
                import chardet
                detected = chardet.detect(raw_bytes[:10000])
                detected_enc = detected.get("encoding")
                if detected_enc:
                    buffer.seek(0)
                    df = pd.read_csv(buffer, encoding=detected_enc, sep=delimiter)
            except Exception:
                pass

        if df is None:
            raise ValueError("Failed to decode and parse CSV/TSV file with supported encodings.")

    # Validate resulting dataframe
    if df.empty:
        raise ValueError("The uploaded dataset contains no rows.")
    if len(df.columns) == 0:
        raise ValueError("The uploaded dataset contains no columns.")

    # Clean column names (strip whitespace and ensure string type)
    df.columns = [str(c).strip() for c in df.columns]

    return df

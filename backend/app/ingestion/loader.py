"""Defensive ingestion helpers for CSV and Excel datasets."""

from __future__ import annotations

import csv
import io
import os
from pathlib import Path
from typing import BinaryIO, TextIO, Union

import pandas as pd

from app.ingestion.structural import validate_structure
from app.profiling.raw_profiler import profile_raw_dataframe
from app.preprocessing.raw_rule_engine import (
    generate_preprocessing_plan_from_raw_profile,
)


FileInput = Union[str, os.PathLike[str], BinaryIO, TextIO]


def validate_file_extension(file_path: str | os.PathLike[str]) -> str:
    """Return a supported lower-case extension or raise ``ValueError``."""

    extension = Path(file_path).suffix.lower().lstrip(".")
    if extension not in {"csv", "xlsx", "xls"}:
        raise ValueError(
            "Unsupported file format. Only CSV and Excel files are supported."
        )
    return extension


def validate_dataframe(df: pd.DataFrame) -> None:
    """Reject a DataFrame that cannot represent a usable dataset."""

    if df.empty:
        raise ValueError("The uploaded dataset is empty.")
    if len(df.columns) == 0:
        raise ValueError("The uploaded dataset contains no columns.")


def _new_report() -> dict:
    return {
        "status": "error",
        "encoding": None,
        "delimiter": None,
        "header_present": None,
        "file_type": None,
        "warnings": [],
        "errors": [],
    }


def _read_input(file_input: FileInput) -> tuple[bytes, str | None, str]:
    """Read an input once and return bytes, extension hint, and display name."""

    if isinstance(file_input, (str, os.PathLike)):
        path = Path(file_input)
        return path.read_bytes(), path.suffix.lower().lstrip("."), path.name

    if not hasattr(file_input, "read"):
        raise TypeError("file_input must be a path or a readable file-like object.")

    name = str(getattr(file_input, "name", "uploaded_file"))
    extension = Path(name).suffix.lower().lstrip(".") or None
    position = file_input.tell() if hasattr(file_input, "tell") else None
    try:
        if position is not None and hasattr(file_input, "seek"):
            file_input.seek(0)
        raw = file_input.read()
    finally:
        if position is not None and hasattr(file_input, "seek"):
            file_input.seek(position)

    if isinstance(raw, str):
        return raw.encode("utf-8"), extension, Path(name).name
    if isinstance(raw, bytes):
        return raw, extension, Path(name).name
    raise TypeError("The file-like object must return text or bytes from read().")


def _detect_encoding(raw: bytes) -> tuple[str, float | None, list[str]]:
    """Detect text encoding, retaining a safe fallback for missing detectors."""

    warnings: list[str] = []
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig", 1.0, warnings

    try:
        import chardet

        result = chardet.detect(raw)
        encoding = result.get("encoding")
        confidence = result.get("confidence")
        if encoding:
            return encoding, confidence, warnings
    except Exception as error:
        warnings.append(f"chardet detection was unavailable: {error}")

    try:
        from charset_normalizer import from_bytes

        match = from_bytes(raw).best()
        if match is not None:
            return match.encoding, float(match.percent_coherence / 100), warnings
    except Exception as error:
        warnings.append(
            f"charset-normalizer detection was unavailable: {error}"
        )

    warnings.append("Encoding detection fell back to UTF-8.")
    return "utf-8", None, warnings


def _sniff_csv(raw: bytes, encoding: str) -> tuple[str, bool, list[str]]:
    """Detect delimiter and header presence with conservative fallbacks."""

    warnings: list[str] = []
    try:
        sample = raw[:1024 * 1024].decode(encoding)
    except (UnicodeDecodeError, LookupError) as error:
        raise ValueError(f"Unable to decode CSV content as {encoding}: {error}") from error

    if not sample.strip():
        raise ValueError("The uploaded CSV file is empty.")

    try:
        delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t|:").delimiter
    except csv.Error:
        delimiter = ","
        warnings.append("Delimiter sniffing failed; comma was used as the fallback.")

    try:
        header_present = bool(csv.Sniffer().has_header(sample))
    except csv.Error:
        header_present = True
        warnings.append("Header detection failed; the first row was treated as a header.")

    return delimiter, header_present, warnings


def _restore_csv_header(
    df: pd.DataFrame,
    raw: bytes,
    encoding: str,
    delimiter: str,
    header_present: bool,
) -> pd.DataFrame:
    """Undo pandas' automatic duplicate-header mangling."""

    if not header_present:
        return df

    sample = raw.decode(encoding)
    header = next(csv.reader(io.StringIO(sample), delimiter=delimiter), [])
    if len(header) == len(df.columns):
        df = df.copy()
        df.columns = header
    return df


def load_file(file_input: FileInput) -> tuple[pd.DataFrame | None, dict]:
    """Safely load one CSV or Excel input and return its ingestion report.

    The report always contains ``status``, ``encoding``, ``delimiter``,
    ``header_present``, ``warnings``, and ``errors``. On failure, the first
    tuple item is ``None`` and the error is recorded instead of propagated.
    """

    report = _new_report()
    try:
        raw, extension, file_name = _read_input(file_input)
        report["file_name"] = file_name
        if extension is None:
            if raw.startswith(b"PK"):
                extension = "xlsx"
            elif raw.startswith(b"\xd0\xcf\x11\xe0"):
                extension = "xls"
            else:
                extension = "csv"
            report["warnings"].append(
                f"No file extension was provided; content was treated as {extension}."
            )
        if extension not in {"csv", "xlsx", "xls"}:
            raise ValueError(
                "Unsupported file format. Provide a .csv, .xlsx, or .xls file."
            )
        report["file_type"] = extension

        if extension == "csv":
            encoding, confidence, detection_warnings = _detect_encoding(raw)
            report["encoding"] = encoding
            report["encoding_confidence"] = confidence
            report["warnings"].extend(detection_warnings)
            delimiter, header_present, sniff_warnings = _sniff_csv(raw, encoding)
            report["delimiter"] = delimiter
            report["header_present"] = header_present
            report["warnings"].extend(sniff_warnings)
            df = pd.read_csv(
                io.BytesIO(raw),
                encoding=encoding,
                delimiter=delimiter,
                header=0 if header_present else None,
                on_bad_lines="error",
                keep_default_na=False,
            )
            df = _restore_csv_header(
                df,
                raw,
                encoding,
                delimiter,
                header_present,
            )
        else:
            report["delimiter"] = None
            report["header_present"] = True
            df = pd.read_excel(
                io.BytesIO(raw),
                sheet_name=0,
                keep_default_na=False,
            )
            report["warnings"].append(
                "Only the first worksheet was loaded from the Excel workbook."
            )

        report["raw_profile"] = profile_raw_dataframe(df)
        df, structural_report = validate_structure(df)
        report["structural"] = structural_report
        if df is None:
            report["errors"].extend(structural_report["errors"])
            return None, report

        report["preprocessing_plan"] = (
            generate_preprocessing_plan_from_raw_profile(
                df,
                report["raw_profile"],
            ).model_dump()
        )

        report["status"] = "success"
        report["rows"] = len(df)
        report["columns"] = len(df.columns)
        return df, report
    except Exception as error:
        report["errors"].append({"type": type(error).__name__, "message": str(error)})
        return None, report


def load_csv(file_input: FileInput) -> tuple[pd.DataFrame | None, dict]:
    """Load a CSV through :func:`load_file`."""

    return load_file(file_input)


def load_excel(file_input: FileInput) -> tuple[pd.DataFrame | None, dict]:
    """Load an Excel workbook through :func:`load_file`."""

    return load_file(file_input)


def get_file_metadata(file_path: str | os.PathLike[str]) -> dict:
    """Return basic metadata for a path without loading its contents."""

    path = Path(file_path)
    return {
        "file_name": path.name,
        "file_extension": path.suffix.lower(),
        "file_size_bytes": path.stat().st_size,
    }

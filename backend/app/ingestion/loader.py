import pandas as pd
from typing import Union
import os


def validate_file_extension(file_path: str) -> str:
    """
    Validate the uploaded file extension.
    """

    extension = file_path.lower().split(".")[-1]

    supported_extensions = {"csv", "xlsx", "xls"}

    if extension not in supported_extensions:
        raise ValueError(
            "Unsupported file format. "
            "Only CSV and Excel files are supported."
        )

    return extension


def validate_dataframe(df: pd.DataFrame) -> None:
    """
    Validate that the loaded DataFrame contains usable data.
    """

    if df.empty:
        raise ValueError(
            "The uploaded dataset is empty."
        )

    if len(df.columns) == 0:
        raise ValueError(
            "The uploaded dataset contains no columns."
        )


def load_csv(file_path: str) -> pd.DataFrame:
    """
    Load a CSV file while handling common text encodings.
    """

    encodings = [
        "utf-8",
        "utf-8-sig",
        "cp1252",
        "latin1",
    ]

    for encoding in encodings:
        try:
            df = pd.read_csv(
                file_path,
                encoding=encoding
            )

            validate_dataframe(df)

            return df

        except UnicodeDecodeError:
            continue

    raise ValueError(
        "Unable to decode the CSV file using supported encodings."
    )


def load_excel(
    file_path: str
) -> dict[str, pd.DataFrame]:
    """
    Load all sheets from an Excel workbook.
    """

    sheets = pd.read_excel(
        file_path,
        sheet_name=None
    )

    for sheet_name, df in sheets.items():
        validate_dataframe(df)

    return sheets


def load_file(
    file_path: str
) -> Union[pd.DataFrame, dict[str, pd.DataFrame]]:
    """
    Load a CSV or Excel file.
    """

    extension = validate_file_extension(file_path)

    if extension == "csv":
        return load_csv(file_path)

    elif extension in {"xlsx", "xls"}:
        return load_excel(file_path)

    raise ValueError("Unable to load the file.")

def get_file_metadata(file_path: str) -> dict :

    return {
        "file_name" : os.path.basename(file_path),
        "file_extension" : os.path.splitext(file_path)[1].lower(),
        "file_size_bytes" : os.path.getsize(file_path),
    } 


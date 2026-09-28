import requests

from config import ANALYZE_ENDPOINT


def analyze_dataset(file):
    """
    Send the uploaded dataset to the FastAPI backend
    and return the generated EDA report.
    """

    files = {
        "file": (
            file.name,
            file.getvalue(),
            file.type,
        )
    }

    response = requests.post(
        ANALYZE_ENDPOINT,
        files=files,
        timeout=300,
    )

    response.raise_for_status()

    return response.json()
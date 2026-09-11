"""
Data validation
"""
import pandas as pd

class Validator:
    """Validate data transformations"""
    
    @staticmethod
    def validate(df: pd.DataFrame) -> bool:
        """Validate data integrity"""
        return len(df) > 0 and len(df.columns) > 0

    @staticmethod
    def compare(before: pd.DataFrame, after: pd.DataFrame) -> dict:
        """Report structural changes that preprocessing must not make."""

        errors = []
        if len(before) != len(after):
            errors.append("Preprocessing changed the row count.")
        if list(before.columns) != list(after.columns):
            errors.append("Preprocessing changed the column names or order.")
        if not Validator.validate(after):
            errors.append("Preprocessing produced an empty dataset.")
        return {"valid": not errors, "errors": errors}

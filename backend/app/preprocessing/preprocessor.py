import pandas as pd

from app.schemas.preprocessing import (
    PreprocessingAction,
    PreprocessingPlan,
    PreprocessingResult,
)


# ============================================================
# Individual preprocessing operations
# ============================================================

def replace_null_like(
    df: pd.DataFrame,
    columns: list[str]
) -> pd.DataFrame:
    """
    Replace textual representations of missing values
    with Pandas NaN.

    The original DataFrame is not modified.
    """

    df = df.copy()

    null_like_values = {
        "",
        "na",
        "n/a",
        "nan",
        "null",
        "none",
        "missing",
    }

    for column in columns:

        if column not in df.columns:
            continue

        def replace_value(value):

            if pd.isna(value):
                return pd.NA

            if isinstance(value, str):
                if value.strip().lower() in null_like_values:
                    return pd.NA

            return value

        df[column] = df[column].map(replace_value)

    return df


def strip_whitespace(
    df: pd.DataFrame,
    columns: list[str]
) -> pd.DataFrame:
    """
    Remove leading and trailing whitespace
    from string values.

    Non-string values are preserved.
    """

    df = df.copy()

    for column in columns:

        if column not in df.columns:
            continue

        df[column] = df[column].map(
            lambda value:
                value.strip()
                if isinstance(value, str)
                else value
        )

    return df


def replace_empty_strings(
    df: pd.DataFrame,
    columns: list[str]
) -> pd.DataFrame:
    """
    Replace empty or whitespace-only strings
    with Pandas NA.
    """

    df = df.copy()

    for column in columns:

        if column not in df.columns:
            continue

        df[column] = df[column].map(
            lambda value:
                pd.NA
                if isinstance(value, str)
                and value.strip() == ""
                else value
        )

    return df


def convert_to_numeric(
    df: pd.DataFrame,
    columns: list[str]
) -> pd.DataFrame:
    """
    Convert selected columns to numeric values.

    Invalid values become NaN.

    This operation should only be called when the
    rule engine has already determined that conversion
    is sufficiently safe.
    """

    df = df.copy()

    for column in columns:

        if column not in df.columns:
            continue

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    return df


def convert_to_datetime(
    df: pd.DataFrame,
    columns: list[str]
) -> pd.DataFrame:
    """
    Convert selected columns to datetime.

    Invalid values become NaT.
    """

    df = df.copy()

    for column in columns:

        if column not in df.columns:
            continue

        df[column] = pd.to_datetime(
            df[column],
            errors="coerce"
        )

    return df


def convert_to_boolean(
    df: pd.DataFrame,
    columns: list[str]
) -> pd.DataFrame:
    """
    Convert common boolean-like values to
    True / False.

    Unknown values are converted to Pandas NA.
    """

    df = df.copy()

    true_values = {
        "true",
        "yes",
        "y",
        "1",
    }

    false_values = {
        "false",
        "no",
        "n",
        "0",
    }

    for column in columns:

        if column not in df.columns:
            continue

        def convert_value(value):

            if pd.isna(value):
                return pd.NA

            if isinstance(value, bool):
                return value

            if isinstance(value, str):

                normalized = value.strip().lower()

                if normalized in true_values:
                    return True

                if normalized in false_values:
                    return False

            if value in [1, 0]:
                return bool(value)

            return pd.NA

        df[column] = df[column].map(convert_value)

    return df


def normalize_case(
    df: pd.DataFrame,
    columns: list[str],
    strategy: str = "lower"
) -> pd.DataFrame:
    """
    Normalize capitalization of string values.

    Supported strategies:
        - lower
        - upper
        - title
    """

    df = df.copy()

    for column in columns:

        if column not in df.columns:
            continue

        def normalize_value(value):

            if not isinstance(value, str):
                return value

            if strategy == "upper":
                return value.upper()

            if strategy == "title":
                return value.title()

            return value.lower()

        df[column] = df[column].map(
            normalize_value
        )

    return df


# ============================================================
# Action executor
# ============================================================

def execute_preprocessing_action(
    df: pd.DataFrame,
    action: PreprocessingAction
) -> tuple[pd.DataFrame, bool]:
    """
    Execute one safe preprocessing action.

    Returns:
        (updated_dataframe, executed)
    """

    action_name = action.action

    if action_name == "replace_null_like":

        return (
            replace_null_like(
                df,
                action.columns
            ),
            True
        )

    if action_name == "strip_whitespace":

        return (
            strip_whitespace(
                df,
                action.columns
            ),
            True
        )

    if action_name == "replace_empty_strings":

        return (
            replace_empty_strings(
                df,
                action.columns
            ),
            True
        )

    if action_name == "convert_to_numeric":

        return (
            convert_to_numeric(
                df,
                action.columns
            ),
            True
        )

    if action_name == "convert_to_datetime":

        return (
            convert_to_datetime(
                df,
                action.columns
            ),
            True
        )

    if action_name == "convert_to_boolean":

        return (
            convert_to_boolean(
                df,
                action.columns
            ),
            True
        )

    if action_name == "normalize_case":

        strategy = action.parameters.get(
            "strategy",
            "lower"
        )

        return (
            normalize_case(
                df,
                action.columns,
                strategy
            ),
            True
        )

    # Unknown or review-only action
    return df, False


# ============================================================
# Complete preprocessing execution
# ============================================================

def preprocess_dataset(
    df: pd.DataFrame,
    plan: PreprocessingPlan
) -> tuple[pd.DataFrame, PreprocessingResult]:
    """
    Execute safe preprocessing actions from a
    PreprocessingPlan.

    Risky / review-only actions are not executed.

    The original DataFrame is never modified.

    Returns:
        cleaned internal DataFrame
        preprocessing execution report
    """

    cleaned_df = df.copy()

    executed_actions = []
    skipped_actions = []
    changes = []

    for action in plan.actions:

        # ----------------------------------------------------
        # Review / preserve actions are never automatically
        # executed.
        # ----------------------------------------------------

        if (
            action.action.startswith("review_")
            or action.action.startswith("preserve_")
        ):

            skipped_actions.append(action)

            changes.append({
                "columns": action.columns,
                "action": action.action,
                "status": "skipped",
                "reason": action.reason,
            })

            continue

        # ----------------------------------------------------
        # Execute safe action
        # ----------------------------------------------------

        updated_df, executed = (
            execute_preprocessing_action(
                cleaned_df,
                action
            )
        )

        if executed:

            cleaned_df = updated_df

            executed_actions.append(action)

            changes.append({
                "columns": action.columns,
                "action": action.action,
                "status": "executed",
                "reason": action.reason,
            })

        else:

            skipped_actions.append(action)

            changes.append({
                "columns": action.columns,
                "action": action.action,
                "status": "skipped",
                "reason": "Unsupported preprocessing action.",
            })

    result = PreprocessingResult(
        executed_actions=executed_actions,
        skipped_actions=skipped_actions,
        changes=changes,
        reasoning=(
            "Safe preprocessing actions from the "
            "preprocessing plan were executed internally. "
            "Risky or review-only actions were skipped."
        ),
        source="preprocessor",
    )

    return cleaned_df, result


# ============================================================
# Profile-driven preprocessing execution
# ============================================================

def execute_preprocessing_plan(
    df: pd.DataFrame,
    plan: PreprocessingPlan,
    data_loss_threshold: float = 0.30,
    case_strategy: str = "lower",
) -> tuple[pd.DataFrame, list[dict]]:
    """Execute a Part 4 plan on a private copy in a fixed safe order.

    Every planned or automatic decision is recorded in ``execution_log``.
    Conversion actions are attempted only when their confidence is at least
    ``0.80``; lower-confidence conversion proposals are skipped for review.
    The input DataFrame is never modified.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Preprocessing requires a pandas DataFrame.")
    if not 0 <= data_loss_threshold <= 1:
        raise ValueError("data_loss_threshold must be between 0 and 1.")
    if case_strategy not in {"lower", "upper", "title"}:
        raise ValueError("case_strategy must be lower, upper, or title.")

    cleaned = df.copy(deep=True)
    execution_log: list[dict] = []
    actions = list(plan.actions)

    def log(columns, action, status, reason, **effect):
        entry = {
            "columns": list(columns),
            "action": action,
            "status": status,
            "reason": reason,
        }
        entry.update(effect)
        execution_log.append(entry)

    def existing_string_columns() -> list[str]:
        return [
            str(column)
            for column in cleaned.columns
            if pd.api.types.is_object_dtype(cleaned[column])
            or pd.api.types.is_string_dtype(cleaned[column])
        ]

    def safe_columns(columns: list[str]) -> list[str]:
        return [column for column in columns if column in cleaned.columns]

    def apply_string_step(action_name, operation, reason):
        for column in existing_string_columns():
            before = int(cleaned[column].notna().sum())
            if before == 0:
                log([column], action_name, "skipped", "Column is entirely null.")
                continue
            before_values = cleaned[column].copy()
            cleaned[column] = operation(cleaned[column])
            changed = int((before_values.astype("string") != cleaned[column].astype("string")).fillna(False).sum())
            log([column], action_name, "executed", reason, values_changed=changed)

    # 1. Strip whitespace from every string/object column.
    apply_string_step(
        "strip_whitespace",
        lambda series: series.map(lambda value: value.strip() if isinstance(value, str) else value),
        "Stripped leading and trailing whitespace from string values.",
    )

    # 2. Report duplicate rows and columns; neither is removed here.
    duplicate_columns = [str(column) for column in cleaned.columns[cleaned.columns.duplicated(keep=False)]]
    if duplicate_columns:
        log(
            duplicate_columns,
            "detect_duplicate_columns",
            "executed",
            "Duplicate columns detected and retained for review; no columns were removed.",
            duplicate_count=len(set(duplicate_columns)),
        )
    else:
        log([], "detect_duplicate_columns", "skipped", "No duplicate columns detected.", duplicate_count=0)

    duplicate_row_count = int(cleaned.duplicated(keep=False).sum())
    if duplicate_row_count:
        log(
            [],
            "detect_duplicate_rows",
            "executed",
            "Duplicate rows detected and retained for review; no rows were removed.",
            duplicate_row_count=duplicate_row_count,
        )
    else:
        log([], "detect_duplicate_rows", "skipped", "No duplicate rows detected.", duplicate_row_count=0)

    # 5-7. Apply only high-confidence conversion proposals with rollback.
    conversion_actions = {
        "convert_to_numeric": pd.to_numeric,
        "convert_to_datetime": lambda series, errors: pd.to_datetime(series, errors=errors, format="mixed"),
        "convert_to_boolean": None,
    }
    conversion_seen: set[tuple[str, str]] = set()
    for action in actions:
        if action.action not in conversion_actions:
            continue
        for column in action.columns:
            key = (action.action, column)
            if key in conversion_seen:
                continue
            conversion_seen.add(key)
            if column not in cleaned.columns:
                log([column], action.action, "skipped", "Column is missing from the DataFrame.")
                continue
            if cleaned[column].isna().all():
                log([column], action.action, "skipped", "Column is entirely null.")
                continue
            if action.confidence < 0.80:
                log([column], action.action, "skipped", "Conversion confidence is below 0.80; manual review is required.", confidence=action.confidence)
                continue

            original = cleaned[column].copy(deep=True)
            null_before = float(cleaned[column].isna().mean())
            if action.action == "convert_to_boolean":
                converted = cleaned[column].map(
                    lambda value: pd.NA
                    if pd.isna(value)
                    else value
                    if isinstance(value, bool)
                    else True
                    if isinstance(value, str) and value.strip().lower() in {"true", "yes", "y", "1"}
                    else False
                    if isinstance(value, str) and value.strip().lower() in {"false", "no", "n", "0"}
                    else pd.NA
                )
            else:
                converted = conversion_actions[action.action](cleaned[column], errors="coerce")
            null_after = float(converted.isna().mean())
            loss = null_after - null_before
            if loss > data_loss_threshold:
                cleaned[column] = original
                log([column], action.action, "rejected", "Conversion would exceed the allowed data-loss threshold; original values were restored.", null_percentage_before=round(null_before * 100, 4), null_percentage_after=round(null_after * 100, 4), data_loss=round(loss, 4), confidence=action.confidence)
            else:
                cleaned[column] = converted
                log([column], action.action, "executed", "High-confidence conversion applied within the data-loss threshold.", null_percentage_before=round(null_before * 100, 4), null_percentage_after=round(null_after * 100, 4), data_loss=round(max(0, loss), 4), confidence=action.confidence)

    # 8. Normalize case only for confirmed categorical proposals.
    for action in actions:
        if action.action not in {"classify_as_categorical", "normalize_case"}:
            continue
        columns = safe_columns(action.columns)
        if action.action == "classify_as_categorical" and action.confidence < 0.80:
            for column in action.columns:
                log([column], action.action, "skipped", "Categorical confidence is below 0.80; manual review is required.", confidence=action.confidence)
            continue
        for column in columns:
            if cleaned[column].isna().all():
                log([column], "normalize_case", "skipped", "Column is entirely null.")
                continue
            if not (
                pd.api.types.is_object_dtype(cleaned[column])
                or pd.api.types.is_string_dtype(cleaned[column])
            ):
                log(
                    [column],
                    "normalize_case",
                    "skipped",
                    "Case normalization applies only to string-like categorical columns.",
                )
                continue
            cleaned[column] = normalize_case(cleaned, [column], case_strategy)[column]
            log([column], "normalize_case", "executed", f"Applied {case_strategy} case normalization to a confirmed categorical column.", strategy=case_strategy)

    # 9. Record all other plan actions, including preserves and review items.
    executed_actions = {(entry["action"], entry["columns"][0]) for entry in execution_log if entry["columns"]}
    for action in actions:
        if action.action in conversion_actions or action.action in {"classify_as_categorical", "normalize_case"}:
            continue
        for column in action.columns or [""]:
            if action.action in {"preserve_identifier", "preserve_free_text"}:
                log([column], action.action, "skipped", "Preservation decision recorded; no transformation was required.", confidence=action.confidence)
            elif action.action.startswith("review_"):
                log([column], action.action, "skipped", "Action requires manual review and was not applied.", confidence=action.confidence)
            elif (action.action, column) not in executed_actions:
                log([column], action.action, "skipped", "Action was not applicable to the fixed execution steps.", confidence=action.confidence)

    return cleaned, execution_log
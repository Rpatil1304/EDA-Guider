from app.schemas.profile import DatasetProfile

from app.schemas.preprocessing import (
    PreprocessingAction,
    PreprocessingPlan,
)


def generate_preprocessing_plan(
    profile: DatasetProfile
) -> PreprocessingPlan:
    """
    Generate preprocessing actions based on
    the observations collected during profiling.

    This function does NOT modify the dataset.
    It only creates a preprocessing plan.

    The rule engine separates:
        - high-confidence transformations
        - potentially risky transformations requiring review
    """

    actions: list[PreprocessingAction] = []

    for column_profile in profile.column_profiles:

        column = column_profile.name
        is_constant = column_profile.is_constant

        # ====================================================
        # 1. Null-like values
        # ====================================================

        if column_profile.null_like_count > 0:

            actions.append(
                PreprocessingAction(
                    columns=[column],
                    action="replace_null_like",
                    reason=(
                        "Null-like values were detected "
                        "in the column."
                    ),
                )
            )

        # ====================================================
        # 2. Leading / trailing whitespace
        # ====================================================

        if column_profile.has_whitespace:

            actions.append(
                PreprocessingAction(
                    columns=[column],
                    action="strip_whitespace",
                    reason=(
                        "Leading or trailing whitespace "
                        "was detected."
                    ),
                )
            )

        # ====================================================
        # 3. Empty strings
        # ====================================================

        if column_profile.has_empty_strings:

            actions.append(
                PreprocessingAction(
                    columns=[column],
                    action="replace_empty_strings",
                    reason=(
                        "Empty or whitespace-only strings "
                        "were detected."
                    ),
                )
            )

        # ====================================================
        # 4. Numeric conversion
        # ====================================================

        numeric_score = (
            column_profile.numeric_parseable_percentage
        )

        if (
            not is_constant
            and numeric_score is not None
            and numeric_score >= 80
        ):

            # ------------------------------------------------
            # Potential ID should never be automatically
            # converted to numeric.
            # ------------------------------------------------

            if column_profile.is_potential_id:

                actions.append(
                    PreprocessingAction(
                        columns=[column],
                        action="preserve_identifier",
                        reason=(
                            "The column is highly numeric-like "
                            "but also appears to be an identifier. "
                            "Automatic numeric conversion is "
                            "therefore avoided."
                        ),
                    )
                )
            elif column_profile.has_mixed_types:

                actions.append(
                    PreprocessingAction(
                        columns=[column],
                        action="review_numeric_conversion",
                        reason=(
                            "The column contains mixed data types. "
                            "Although many values are numeric-like, "
                            "automatic conversion may result in data loss."
                        ),
                        parameters={
                            "numeric_parseable_percentage":
                                numeric_score
                        },
                    )
                )

            # ------------------------------------------------
            # Strongly numeric semantic type
            # ------------------------------------------------

            elif (
                not column_profile.has_mixed_types
                and column_profile.inferred_type in [
                    "integer",
                    "float",
                    "numeric",
                ]
            ):

                actions.append(
                    PreprocessingAction(
                        columns=[column],
                        action="convert_to_numeric",
                        reason=(
                            "The column has a high numeric "
                            "parseability percentage and its "
                            "semantic type is numeric."
                        ),
                        parameters={
                            "threshold": 80
                        },
                    )
                )

            # ------------------------------------------------
            # Numeric-like but semantic type is uncertain.
            # Do NOT silently convert.
            # ------------------------------------------------

            else:

                actions.append(
                    PreprocessingAction(
                        columns=[column],
                        action="review_numeric_conversion",
                        reason=(
                            "The column contains many values "
                            "that can be interpreted as numeric, "
                            "but its semantic type is not "
                            "confidently numeric."
                        ),
                        parameters={
                            "numeric_parseable_percentage":
                                numeric_score
                        },
                    )
                )

        # ====================================================
        # 5. Datetime conversion
        # ====================================================

        datetime_score = (
            column_profile.datetime_parseable_percentage
        )

        if (
            datetime_score is not None
            and datetime_score >= 80
        ):

            if column_profile.inferred_type == "datetime":

                actions.append(
                    PreprocessingAction(
                        columns=[column],
                        action="convert_to_datetime",
                        reason=(
                            "The column has a high datetime "
                            "parseability percentage and is "
                            "classified as datetime-like."
                        ),
                        parameters={
                            "threshold": 80
                        },
                    )
                )

            else:

                actions.append(
                    PreprocessingAction(
                        columns=[column],
                        action="review_datetime_conversion",
                        reason=(
                            "Many values appear to be "
                            "datetime-like, but the semantic "
                            "type is not confidently datetime."
                        ),
                        parameters={
                            "datetime_parseable_percentage":
                                datetime_score
                        },
                    )
                )

        # ====================================================
        # 6. Boolean conversion
        # ====================================================

        boolean_score = (
            column_profile.boolean_parseable_percentage
        )

        if (
            not is_constant
            and boolean_score is not None
            and boolean_score >= 80
        ):

            if column_profile.inferred_type == "boolean":

                actions.append(
                    PreprocessingAction(
                        columns=[column],
                        action="convert_to_boolean",
                        reason=(
                            "The column has a high boolean "
                            "parseability percentage and is "
                            "classified as boolean-like."
                        ),
                        parameters={
                            "threshold": 80
                        },
                    )
                )

            else:

                actions.append(
                    PreprocessingAction(
                        columns=[column],
                        action="review_boolean_conversion",
                        reason=(
                            "Many values appear to be "
                            "boolean-like, but the semantic "
                            "type is not confidently boolean."
                        ),
                        parameters={
                            "boolean_parseable_percentage":
                                boolean_score
                        },
                    )
                )

        # ====================================================
        # 7. Case normalization
        # ====================================================

        if (
            column_profile.has_case_variations
            and column_profile.inferred_type
            in ["categorical", "text"]
        ):

            actions.append(
                PreprocessingAction(
                    columns=[column],
                    action="normalize_case",
                    reason=(
                        "Different capitalization patterns "
                        "were detected in a categorical/text "
                        "column."
                    ),
                    parameters={
                        "strategy": "lower"
                    },
                )
            )

        # ====================================================
        # 8. Constant column
        # ====================================================

        if column_profile.is_constant:

            actions.append(
                PreprocessingAction(
                    columns=[column],
                    action="review_constant_column",
                    reason=(
                        "The column contains only one "
                        "distinct non-null value."
                    ),
                )
            )

        # ====================================================
        # 9. Potential ID
        # ====================================================

        # Avoid creating duplicate preserve_identifier
        # actions if numeric conversion already detected
        # the potential ID above.

        if (
            column_profile.is_potential_id
            and not (
                numeric_score is not None
                and numeric_score >= 80
            )
        ):

            actions.append(
                PreprocessingAction(
                    columns=[column],
                    action="preserve_identifier",
                    reason=(
                        "The column appears to be an "
                        "identifier."
                    ),
                )
            )

        # ====================================================
        # 10. Statistical outliers
        # ====================================================

        if column_profile.outlier_count > 0:

            actions.append(
                PreprocessingAction(
                    columns=[column],
                    action="review_outliers",
                    reason=(
                        "Statistical outliers were detected. "
                        "They should be reviewed rather than "
                        "automatically removed."
                    ),
                    parameters={
                        "outlier_count":
                            column_profile.outlier_count,
                        "outlier_percentage":
                            column_profile.outlier_percentage,
                    },
                )
            )

    # ========================================================
    # Final preprocessing plan
    # ========================================================

    return PreprocessingPlan(
        actions=actions,

        reasoning=(
            "Preprocessing actions were generated from "
            "dataset profiling observations. High-confidence "
            "transformations are recommended automatically, "
            "while ambiguous type conversions and potentially "
            "destructive operations are flagged for review."
        ),

        source="rule_engine",
    )
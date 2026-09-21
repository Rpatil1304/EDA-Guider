from app.langchain.model import (
    validate_visualization_recommendations,
)


# ================================================================
# Sample Statistical Evidence
# ================================================================

test_statistical_profile = {
    "n_rows": 100,
    "n_cols": 11,

    "columns": {
        "age": {
            "name": "age",
            "inferred_type": "numeric",
            "count": 100,
            "missing_count": 0,
            "unique_count": 42,
            "numeric": {
                "mean": 38.5,
                "median": 37.0,
                "std": 11.2,
                "minimum": 18.0,
                "maximum": 65.0,
                "skewness": 0.15,
                "kurtosis": -0.45,
            },
        },

        "salary": {
            "name": "salary",
            "inferred_type": "numeric",
            "count": 100,
            "missing_count": 0,
            "unique_count": 96,
            "numeric": {
                "mean": 85000.0,
                "median": 78000.0,
                "std": 32000.0,
                "minimum": 25000.0,
                "maximum": 180000.0,
                "skewness": 1.2,
                "kurtosis": 1.8,
            },
        },

        "city": {
            "name": "city",
            "inferred_type": "categorical",
            "count": 100,
            "missing_count": 0,
            "unique_count": 9,
            "categorical": {
                "top": "mumbai",
                "top_frequency": 20,
                "top_percentage": 20.0,
            },
        },
    },

    "correlation_matrix": {
        "age": {
            "age": 1.0,
            "salary": 0.72,
        },
        "salary": {
            "age": 0.72,
            "salary": 1.0,
        },
    },
}


# ================================================================
# Rule-Based Recommendations
# ================================================================

test_rule_recommendations = [

    {
        "rule_id": "NUMERIC_HISTOGRAM",
        "chart_type": "histogram",
        "columns": ["age"],
        "reason": (
            "Age is a numeric variable and its distribution "
            "should be examined."
        ),
        "confidence": 0.95,
        "priority": "high",
    },

    {
        "rule_id": "NUMERIC_HISTOGRAM",
        "chart_type": "histogram",
        "columns": ["salary"],
        "reason": (
            "Salary is a numeric variable and its distribution "
            "should be examined."
        ),
        "confidence": 0.95,
        "priority": "high",
    },

    {
        "rule_id": "NUMERIC_NUMERIC_SCATTER",
        "chart_type": "scatter_plot",
        "columns": ["age", "salary"],
        "reason": (
            "Both age and salary are numeric variables, making "
            "a scatter plot suitable for examining their relationship."
        ),
        "confidence": 0.90,
        "priority": "high",
    },

    {
        "rule_id": "CATEGORICAL_BAR",
        "chart_type": "bar_chart",
        "columns": ["city"],
        "reason": (
            "City is a categorical variable with 9 unique values, "
            "making a bar chart suitable for comparing frequencies."
        ),
        "confidence": 0.95,
        "priority": "high",
    },

    {
        "rule_id": "LOW_CARDINALITY_PIE",
        "chart_type": "pie_chart",
        "columns": ["city"],
        "reason": (
            "City has relatively low cardinality, so a pie chart "
            "can show the categorical distribution."
        ),
        "confidence": 0.85,
        "priority": "medium",
    },
]


# ================================================================
# Run Validation
# ================================================================

result = validate_visualization_recommendations(
    statistical_profile=test_statistical_profile,
    visualization_recommendations=test_rule_recommendations,
)


# ================================================================
# Display Result
# ================================================================

print()
print("=" * 80)
print("LLM VISUALIZATION VALIDATION RESPONSE")
print("=" * 80)

print(
    result.model_dump_json(
        indent=2
    )
)
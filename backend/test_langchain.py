from app.langchain.model import (
    generate_llm_visualization_recommendations,
)


def main():
    test_evidence_groups = {
        "NUMERIC_HISTOGRAM": [
            {
                "rule_id": "NUMERIC_HISTOGRAM",
                "chart_type": "histogram",
                "columns": ["age"],
                "confidence": 0.95,
                "priority": "high",
                "reason": "Age is a numeric variable.",
                "row_count": 100,
                "column_statistics": {
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
                    }
                },
            },
            {
                "rule_id": "NUMERIC_HISTOGRAM",
                "chart_type": "histogram",
                "columns": ["salary"],
                "confidence": 0.95,
                "priority": "high",
                "reason": "Salary is a numeric variable.",
                "row_count": 100,
                "column_statistics": {
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
                    }
                },
            },
        ],
        "CATEGORICAL_BAR": [
            {
                "rule_id": "CATEGORICAL_BAR",
                "chart_type": "bar_chart",
                "columns": ["city"],
                "confidence": 0.95,
                "priority": "high",
                "reason": "City is a categorical variable.",
                "row_count": 100,
                "column_statistics": {
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
                    }
                },
            }
        ],
    }

    response = generate_llm_visualization_recommendations(
        test_evidence_groups
    )

    print("\n" + "=" * 80)
    print("LLM VISUALIZATION RESPONSE")
    print("=" * 80)

    print(
        response.model_dump_json(
            indent=2
        )
    )


if __name__ == "__main__":
    main()
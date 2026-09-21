"""Hugging Face + LangChain visualization validation workflow."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables import RunnableParallel

from langchain_huggingface import ChatHuggingFace
from langchain_huggingface import HuggingFaceEndpoint

from app.langchain.schemas import (
    LLMVisualizationValidationResponse,
)


load_dotenv()


# ================================================================
# Model
# ================================================================

def get_huggingface_model() -> ChatHuggingFace:
    """Create and return the Hugging Face chat model."""

    huggingface_token = os.getenv(
        "HUGGINGFACEHUB_API_TOKEN"
    )

    if not huggingface_token:
        raise ValueError(
            "HUGGINGFACEHUB_API_TOKEN environment variable "
            "is not set."
        )

    llm = HuggingFaceEndpoint(
        repo_id="openai/gpt-oss-120b",
        task="text-generation",
        huggingfacehub_api_token=huggingface_token,
        max_new_tokens=2048,
        temperature=0.0,
    )

    return ChatHuggingFace(
        llm=llm,
    )


# ================================================================
# Parser
# ================================================================

def get_visualization_output_parser() -> PydanticOutputParser:
    """Create the Pydantic output parser."""

    return PydanticOutputParser(
        pydantic_object=LLMVisualizationValidationResponse
    )


# ================================================================
# Prompt
# ================================================================

def get_visualization_prompt() -> ChatPromptTemplate:
    """Create the visualization validation prompt."""

    parser = get_visualization_output_parser()

    system_message = """
You are an expert exploratory data analysis assistant.

Your task is to validate visualization recommendations produced
by a deterministic rule-based EDA engine.

You are a recommendation and decision-support system.

You MUST NOT:
- generate or render charts
- execute Python code
- modify the dataset
- perform preprocessing
- invent dataset values
- assume information that is not present in the evidence
- recommend columns that are not present in the evidence

The deterministic rule-based engine has already analyzed the
dataset and produced visualization recommendations.

Your task is to REVIEW those recommendations using the provided
statistical evidence.

For every rule-based recommendation, make one decision:

1. accepted
   Use this when the recommended visualization is appropriate.

2. modified
   Use this when the general visualization idea is appropriate
   but the chart type or columns should be changed.

3. rejected
   Use this when the visualization is not appropriate for the
   available evidence.

IMPORTANT:

- Do not automatically reject rule-based recommendations.
- Keep a recommendation as "accepted" when it is already suitable.
- Only modify or reject a recommendation when the statistical
  evidence provides a clear reason.
- Use the exact dataset column names.
- Do not invent columns.
- The final chart type must be one of the supported chart types.
- The final columns must exist in the provided evidence.
- If the decision is "accepted", final_chart_type should normally
  be the same as original_chart_type.
- If the decision is "modified", provide the corrected chart type
  and columns.
- If the decision is "rejected", final_chart_type must be null
  and final_columns must be an empty list.
- Provide a confidence value between 0 and 1.
- Explain the reasoning briefly and clearly.

Supported chart types:

histogram
box_plot
bar_chart
pie_chart
scatter_plot
line_chart
grouped_bar_chart
stacked_bar_chart
100_percent_stacked_bar_chart
heatmap
missingness_bar_chart
missingness_heatmap
violin_plot
qq_plot
pair_plot

Return ONLY valid JSON.

Every confidence value MUST be a numeric decimal between 0 and 1.

Do not use words for confidence values.

Do not include markdown.

Do not include explanations outside the JSON object.

Do not add trailing commas.

Do not change the required field names.

Return only the JSON object required by the format instructions.

{format_instructions}
"""

    human_message = """
The following information contains:

1. Privacy-safe statistical evidence about the dataset.
2. Visualization recommendations produced by the deterministic
   rule-based engine.

Review every rule-based recommendation and validate it using the
statistical evidence.

STATISTICAL EVIDENCE:

{statistical_evidence}

RULE-BASED VISUALIZATION RECOMMENDATIONS:

{rule_recommendations}

Return one validation result for every rule-based recommendation.
"""

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_message,
            ),
            (
                "human",
                human_message,
            ),
        ]
    ).partial(
        format_instructions=parser.get_format_instructions()
    )


# ================================================================
# Runnable Chain
# ================================================================

def build_visualization_validation_chain():
    """Build the LangChain Runnable visualization validation chain."""

    prompt = get_visualization_prompt()

    model = get_huggingface_model()

    parser = get_visualization_output_parser()

    prepare_input = RunnableParallel(
        statistical_evidence=RunnableLambda(
            lambda data: data["statistical_evidence"]
        ),
        rule_recommendations=RunnableLambda(
            lambda data: data["rule_recommendations"]
        ),
    )

    chain = (
        prepare_input
        | prompt
        | model
        | parser
    )

    return chain


# ================================================================
# Main Validation Function
# ================================================================

def validate_visualization_recommendations(
    statistical_profile: dict[str, Any],
    visualization_recommendations: list[dict[str, Any]],
) -> LLMVisualizationValidationResponse:
    """
    Validate deterministic visualization recommendations using
    privacy-safe statistical evidence and Hugging Face through
    LangChain.
    """

    chain = build_visualization_validation_chain()

    prepared_input = prepare_visualization_validation_input(
        statistical_profile,
        visualization_recommendations,
    )

    return chain.invoke(
        prepared_input
    )


# ================================================================
# Input Preparation
# ================================================================

def prepare_visualization_validation_input(
    statistical_profile: dict[str, Any],
    visualization_recommendations: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Prepare privacy-safe input for visualization validation.

    Only structured statistical information and deterministic
    recommendation metadata are provided to the LLM.
    """

    statistical_evidence = {
        "row_count": statistical_profile.get(
            "n_rows",
            0,
        ),
        "column_count": statistical_profile.get(
            "n_cols",
            0,
        ),
        "columns": statistical_profile.get(
            "columns",
            {},
        ),
        "correlation_matrix": statistical_profile.get(
            "correlation_matrix",
            {},
        ),
    }

    rule_recommendations = []

    for recommendation in visualization_recommendations:
        rule_recommendations.append(
            {
                "rule_id": recommendation.get(
                    "rule_id"
                ),
                "chart_type": recommendation.get(
                    "chart_type"
                ),
                "columns": recommendation.get(
                    "columns",
                    [],
                ),
                "reason": recommendation.get(
                    "reason",
                    "",
                ),
                "confidence": recommendation.get(
                    "confidence",
                    0.0,
                ),
                "priority": recommendation.get(
                    "priority",
                    "medium",
                ),
            }
        )

    return {
        "statistical_evidence": statistical_evidence,
        "rule_recommendations": rule_recommendations,
    }


"""Hugging Face + LangChain visualization recommendation workflow."""

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
    LLMVisualizationResponse,
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
        max_new_tokens=1024,
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
        pydantic_object=LLMVisualizationResponse
    )


# ================================================================
# Prompt
# ================================================================

def get_visualization_prompt() -> ChatPromptTemplate:
    """Create the visualization recommendation prompt."""

    parser = get_visualization_output_parser()

    system_message = """
You are an expert exploratory data analysis assistant.

Your task is to recommend suitable visualizations for a dataset
based only on the structured statistical evidence provided to you.

You are a recommendation and decision-support system.

You MUST NOT:
- generate or render charts
- execute Python code
- modify the dataset
- perform preprocessing
- invent dataset values
- assume information that is not present in the evidence
- recommend columns that are not present in the evidence

You SHOULD:
- analyze the provided statistical evidence
- independently recommend useful visualizations
- select appropriate chart types
- identify the relevant dataset columns
- explain why each visualization is useful
- provide a confidence value between 0 and 1
- avoid unnecessary or redundant visualizations
- use the exact column names provided in the evidence

A deterministic rule-based visualization engine has already
produced recommendations separately.

You are NOT required to agree with those recommendations.

Your role is to independently reason about the evidence and
produce your own visualization recommendations.

Return only the required structured output.

{format_instructions}
"""

    human_message = """
Here is the structured visualization evidence for the dataset:

{visualization_evidence}

Analyze this evidence and provide your independent visualization
recommendations.
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

def build_visualization_chain():
    """Build the LangChain Runnable visualization chain."""

    prompt = get_visualization_prompt()

    model = get_huggingface_model()

    parser = get_visualization_output_parser()

    prepare_input = RunnableParallel(
        visualization_evidence=RunnableLambda(
            lambda evidence: evidence
        )
    )

    chain = (
        prepare_input
        | prompt
        | model
        | parser
    )

    return chain


# ================================================================
# Main LangChain Recommendation Function
# ================================================================

def generate_llm_visualization_recommendations(
    visualization_evidence: Any,
) -> LLMVisualizationResponse:
    """
    Generate independent visualization recommendations using
    Hugging Face through LangChain.
    """

    chain = build_visualization_chain()

    return chain.invoke(
        prepare_llm_visualization_evidence(
            visualization_evidence
        )
    )

def prepare_llm_visualization_evidence(
    visualization_evidence_groups: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """
    Prepare privacy-safe statistical evidence for the LLM.

    Rule-engine recommendation metadata is intentionally removed so
    that the LLM can independently reason about suitable charts.
    """

    row_count = 0
    columns: dict[str, dict[str, Any]] = {}

    for evidence_items in visualization_evidence_groups.values():
        for evidence in evidence_items:

            if row_count == 0:
                row_count = evidence.get("row_count", 0)

            column_statistics = evidence.get(
                "column_statistics",
                {},
            )

            for column_name, statistics in column_statistics.items():
                columns[column_name] = statistics

    return {
        "row_count": row_count,
        "columns": columns,
    }
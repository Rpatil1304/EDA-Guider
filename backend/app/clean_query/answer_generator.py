"""Natural language answer generator module for clean dataset queries.

Synthesizes raw Python execution outputs, calculations, and chart details
into a clear, professional, natural-language explanation for the user.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from app.llm_client import (
    invoke_gemini_prompt,
    get_model_name as get_default_model,
)


def generate_natural_language_answer(
    user_query: str,
    execution_result: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
    model_name: Optional[str] = None,
) -> str:
    """Generate a conversational, direct answer from query execution results.

    Parameters
    ----------
    user_query : str
        Original natural language question from the user.
    execution_result : Dict[str, Any]
        Output dictionary from executor.py containing status, result_string,
        result_data, has_figure, etc.
    metadata : Optional[Dict[str, Any]]
        Dataset metadata context.
    model_name : Optional[str]
        Optional Gemini model name override.

    Returns
    -------
    str
        Natural language answer formatted in Markdown.
    """
    status = execution_result.get("status", "error")

    # If execution failed completely, provide clear guidance
    if status != "success":
        error_msg = execution_result.get("error", "Unknown error occurred.")
        return (
            f"I encountered an issue computing the answer for your query: **\"{user_query}\"**.\n\n"
            f"**Details**: {error_msg}\n\n"
            "Please check if the requested metrics or columns match the uploaded dataset, "
            "or rephrase your question."
        )

    # Extract execution details
    result_str = execution_result.get("result_string") or ""
    stdout_str = execution_result.get("stdout") or ""
    has_figure = execution_result.get("has_figure", False)

    computed_context_parts = []
    if result_str and result_str != "None":
        computed_context_parts.append(f"COMPUTED RESULT / DATA:\n{result_str}")
    if stdout_str:
        computed_context_parts.append(f"CONSOLE OUTPUT:\n{stdout_str}")
    if has_figure:
        computed_context_parts.append("VISUALIZATION: An interactive chart was successfully generated.")

    computed_context = "\n\n".join(computed_context_parts) if computed_context_parts else "No specific value returned."

    system_instruction = """You are a senior data analyst and insights communicator.
Given a user query and the exact computed results produced by executing Python code against the dataset,
provide a clear, direct, and conversational natural-language answer.

GUIDELINES:
1. Answer directly and naturally (avoid phrases like "Based on the Python output..." or "The code returned...").
2. Explicitly cite the key numbers, names, or values from the computed data.
3. Use markdown formatting (bolding, bullet points) to make tables or lists easy to read.
4. Keep the answer concise and insightful (typically 2-4 sentences or a short bulleted list).
5. If an interactive chart was generated, mention what the chart highlights or visualizes.
"""

    prompt = f"""USER QUESTION:
"{user_query}"

{computed_context}

Provide a direct, helpful answer:"""

    try:
        answer = invoke_gemini_prompt(
            system_instruction=system_instruction,
            user_prompt=prompt,
            temperature=0.2,
            model_name=model_name,
        )
        if answer and answer.strip():
            return answer.strip()
    except Exception as exc:
        # Fallback if LLM formatting fails: return raw result gracefully
        pass

    # Clean fallback without LLM
    if result_str:
        return f"**Result for \"{user_query}\"**:\n\n{result_str}"
    elif has_figure:
        return "Interactive visualization generated successfully."
    else:
        return "Query executed successfully."

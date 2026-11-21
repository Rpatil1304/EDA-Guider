"""Centralized LLM client and configuration module.

Provides a unified Google Gemini client and configuration for both:
- RAW section (2 LLM stages: Visualization Validation & Final Report Generation)
- CLEAN section (1 LLM stage: Query Code Generation & Answer Synthesis)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# Locate and load .env from backend directory or project root
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"

if _ENV_FILE.is_file():
    load_dotenv(_ENV_FILE)
else:
    load_dotenv()


def get_google_api_key() -> str:
    """Retrieve and validate the Google API key."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY is not set. Please add GOOGLE_API_KEY to your backend/.env file."
        )
    return api_key


def get_model_name(default: str = "gemini-3.1-flash-lite-preview") -> str:
    """Return configured Gemini model name."""
    return os.getenv("GEMINI_MODEL", default)


def get_genai_client() -> genai.Client:
    """Return an initialized Google GenAI direct client."""
    return genai.Client(api_key=get_google_api_key())


# Alias for convenience
get_gemini_client = get_genai_client


def get_google_chat_model(
    temperature: float = 0.0,
    max_output_tokens: int = 4096,
    model_name: Optional[str] = None,
) -> ChatGoogleGenerativeAI:
    """Return an initialized LangChain ChatGoogleGenerativeAI chat model."""
    selected_model = model_name or get_model_name()
    return ChatGoogleGenerativeAI(
        model=selected_model,
        google_api_key=get_google_api_key(),
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )


def invoke_gemini_prompt(
    system_instruction: str,
    user_prompt: str,
    temperature: float = 0.0,
    max_output_tokens: int = 4096,
    model_name: Optional[str] = None,
) -> str:
    """Unified invocation helper for Google Gemini using ChatGoogleGenerativeAI.

    Provides a clean, reliable, and shared interface across both RAW and CLEAN pipelines.
    """
    llm = get_google_chat_model(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        model_name=model_name,
    )
    messages = [
        SystemMessage(content=system_instruction),
        HumanMessage(content=user_prompt),
    ]
    resp = llm.invoke(messages)
    content = resp.content
    if isinstance(content, list):
        return "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    return str(content)

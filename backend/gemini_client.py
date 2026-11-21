"""LangChain Gemini client initialization and safe error translation."""

from __future__ import annotations

from langchain_google_genai import ChatGoogleGenerativeAI

from backend.config import MissingConfigError, get_gemini_config


def get_gemini_llm(temperature: float = 0.2) -> ChatGoogleGenerativeAI:
    """Create a configured ChatGoogleGenerativeAI instance using env-only credentials."""
    config = get_gemini_config()
    return ChatGoogleGenerativeAI(
        model=config.model,
        google_api_key=config.api_key,
        temperature=temperature,
    )


def format_gemini_error(exc: Exception) -> str:
    """Convert raw Gemini/LangChain exceptions into safe, user-friendly guidance."""
    if isinstance(exc, MissingConfigError):
        return str(exc)

    msg = str(exc).lower()
    if "api_key_invalid" in msg or "api key not valid" in msg or "403" in msg or "permission_denied" in msg:
        return (
            "Your Gemini API key appears invalid or lacks permission. "
            "Please double-check `GEMINI_API_KEY` in your `.env` file."
        )
    if "not_found" in msg or "404" in msg or "is not found for api version" in msg:
        return (
            "The configured `GEMINI_MODEL` could not be found. "
            "Please check `GEMINI_MODEL` in your `.env` file (for example `gemini-2.5-flash`)."
        )
    if "resource_exhausted" in msg or "429" in msg or "quota" in msg:
        return (
            "Gemini API rate limit or quota was reached. Please wait a moment and try again, "
            "or check your Google AI Studio quota."
        )
    if "timeout" in msg or "connection" in msg or "unavailable" in msg:
        return "Could not reach the Gemini service due to a network timeout. Please try again in a moment."

    return "The AI assistant encountered an error while contacting Gemini. Please check your configuration and try again."

"""Environment and Gemini configuration loader for Desi Bites."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

_PLACEHOLDER_KEYS = {
    "",
    "MY_GEMINI_API_KEY",
    "YOUR_GEMINI_API_KEY",
    "your_api_key_here",
    "your-gemini-api-key",
    "REPLACE_ME",
}


class MissingConfigError(RuntimeError):
    """Raised when required environment configuration such as GEMINI_API_KEY is missing."""


@dataclass(frozen=True)
class GeminiConfig:
    """Validated Gemini runtime configuration."""

    api_key: str
    model: str


def reload_environment() -> None:
    """Load variables from local .env file without overriding explicit process env vars."""
    load_dotenv(dotenv_path=ENV_FILE_PATH, override=False)


def get_gemini_model_name() -> str:
    """Return configured GEMINI_MODEL or default configurable model alias."""
    reload_environment()
    configured = os.getenv("GEMINI_MODEL", "").strip()
    return configured if configured else DEFAULT_GEMINI_MODEL


def get_gemini_config() -> GeminiConfig:
    """Read GEMINI_API_KEY and GEMINI_MODEL exclusively from environment configuration.

    Raises MissingConfigError if GEMINI_API_KEY is missing or left as a placeholder.
    """
    reload_environment()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key in _PLACEHOLDER_KEYS:
        raise MissingConfigError(
            "GEMINI_API_KEY is not configured. Please create a `.env` file from `.env.example` "
            "and add your own Gemini API key (`GEMINI_API_KEY=...`)."
        )

    model = get_gemini_model_name()
    return GeminiConfig(api_key=api_key, model=model)


def is_gemini_configured() -> tuple[bool, str | None]:
    """Return (True, None) when GEMINI_API_KEY is available, else (False, helpful_message)."""
    try:
        get_gemini_config()
        return True, None
    except MissingConfigError as exc:
        return False, str(exc)

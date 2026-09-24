"""Env-gated Anthropic client.

The whole app must work without an API key: callers catch
LLMNotConfiguredError and degrade (manual biomarker entry, template reports).

Requests enable the server-side refusal fallback (`fallbacks: "default"`) so a
safety-classifier decline is retried on Anthropic's recommended fallback model
within the same call.
"""

import anthropic

from src.core.config import settings

MODEL = "claude-opus-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class LLMNotConfiguredError(RuntimeError):
    """Raised when an LLM feature is used without ANTHROPIC_API_KEY set."""


class LLMRefusedError(RuntimeError):
    """Raised when the model (and its fallback chain) declined the request."""


def llm_available() -> bool:
    return bool(settings.anthropic_api_key)


def get_client() -> anthropic.Anthropic:
    if not llm_available():
        raise LLMNotConfiguredError(
            "ANTHROPIC_API_KEY is not set — add it to .env to enable OCR "
            "extraction and report phrasing. All other features work without it."
        )
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def check_refusal(response) -> None:
    if response.stop_reason == "refusal":
        raise LLMRefusedError("The model declined this request.")

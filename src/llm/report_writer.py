"""Assessment → plain-language patient report (Bangla or English).

Runs once, before approval: the reviewing physician asks for the wording,
reads it, and approves it together with the plan (src/api/report_wording.py).
The approved text is stored and is what the patient reads; nothing here runs
when a report is opened. This module just phrases what it is given.
"""

import json
from pathlib import Path

import anthropic

from src.llm.client import (
    FALLBACK_BETA,
    MODEL,
    LLMIncompleteError,
    LLMUnavailableError,
    check_refusal,
    get_client,
)

_PROMPTS = Path(__file__).resolve().parent / "prompts"


def write_report(patient_name: str, approved_result: dict, lang: str = "en") -> str:
    """Phrase the assessment for the patient. Raises LLMNotConfiguredError
    without an API key, LLMUnavailableError when the API cannot be reached or
    answers with an error, LLMRefusedError when the model declines, and
    LLMIncompleteError when the reply stops before its end: a report cut off
    part-way is never returned as if it were whole."""
    client = get_client()
    language = "Bangla" if lang == "bn" else "English"

    try:
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=8192,
            betas=[FALLBACK_BETA],
            fallbacks="default",
            system=(_PROMPTS / "report_system.txt").read_text(encoding="utf-8"),
            messages=[{
                "role": "user",
                "content": (
                    f"Language: {language}\n"
                    f"Patient name: {patient_name}\n\n"
                    "Physician-approved assessment (JSON):\n"
                    f"{json.dumps(approved_result, ensure_ascii=False, indent=2)}"
                ),
            }],
        )
    except anthropic.RateLimitError as exc:
        raise LLMUnavailableError("The AI service is rate-limited at the moment.") from exc
    except anthropic.APIStatusError as exc:
        raise LLMUnavailableError(
            f"The AI service answered with an error ({exc.status_code}).") from exc
    except anthropic.APIConnectionError as exc:  # timeouts included
        raise LLMUnavailableError("The AI service could not be reached.") from exc
    check_refusal(response)
    if response.stop_reason == "max_tokens":
        raise LLMIncompleteError("The AI wording was cut off before its end.")
    text = next((block.text for block in response.content if block.type == "text"), "").strip()
    if not text:
        raise LLMIncompleteError("The AI returned no wording.")
    return text

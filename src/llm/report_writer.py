"""Approved assessment → plain-language patient report (Bangla or English).

Only runs on assessments that already carry a physician Approval — the API
layer enforces that gate; this module just phrases what was approved.
"""

import json
from pathlib import Path

from src.llm.client import FALLBACK_BETA, MODEL, check_refusal, get_client

_PROMPTS = Path(__file__).resolve().parent / "prompts"


def write_report(patient_name: str, approved_result: dict, lang: str = "en") -> str:
    """Phrase the approved assessment for the patient. Raises
    LLMNotConfiguredError without an API key."""
    client = get_client()
    language = "Bangla" if lang == "bn" else "English"

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
    check_refusal(response)
    return next(b.text for b in response.content if b.type == "text")

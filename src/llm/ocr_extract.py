"""Lab-report image → structured biomarker values (physician-confirmed prefill).

The extracted values are never scored directly: the API returns them to the
intake form, where the physician reviews and confirms each one before any
clinical rule runs.
"""

import base64
import json
from pathlib import Path

from pydantic import BaseModel

from src.llm.client import FALLBACK_BETA, MODEL, check_refusal, get_client

_PROMPTS = Path(__file__).resolve().parent / "prompts"


class ExtractedBiomarkers(BaseModel):
    fasting_glucose: float | None = None  # mg/dL
    systolic_bp: float | None = None      # mmHg
    diastolic_bp: float | None = None     # mmHg
    hemoglobin: float | None = None       # g/dL
    notes: str = ""


_number_or_null = {"anyOf": [{"type": "number"}, {"type": "null"}]}

_SCHEMA = {
    "type": "object",
    "properties": {
        "fasting_glucose": _number_or_null,
        "systolic_bp": _number_or_null,
        "diastolic_bp": _number_or_null,
        "hemoglobin": _number_or_null,
        "notes": {"type": "string"},
    },
    "required": ["fasting_glucose", "systolic_bp", "diastolic_bp", "hemoglobin", "notes"],
    "additionalProperties": False,
}


def extract_biomarkers(image_bytes: bytes, media_type: str) -> ExtractedBiomarkers:
    """OCR a lab-report image. Raises LLMNotConfiguredError without an API key."""
    client = get_client()
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=4096,
        betas=[FALLBACK_BETA],
        fallbacks="default",
        system=(_PROMPTS / "ocr_system.txt").read_text(encoding="utf-8"),
        output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": image_b64},
                },
                {"type": "text", "text": "Extract the biomarker values from this lab report."},
            ],
        }],
    )
    check_refusal(response)
    text = next(b.text for b in response.content if b.type == "text")
    return ExtractedBiomarkers.model_validate(json.loads(text))

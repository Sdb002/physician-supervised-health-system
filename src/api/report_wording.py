"""The wording of a patient's report: written before approval, read by the
physician, kept with the approval.

A report used to be worded each time it was opened, after the approval, so a
patient could read text (the LLM's, when one was configured) that the
physician had never seen, and different text on the next visit to the page.
Now the wording exists before the decision does:

1. The reviewing physician asks for it (`POST /review/{id}/wording`).
   `prepare()` writes it in both languages from the plan as the physician has
   it, edits and comment included: with the LLM when one is configured and
   wanted, otherwise - or when the LLM declines, fails or is cut off - with
   the deterministic template. It is kept on the assessment as a draft.
2. The physician reads it and approves. `approved()` lets the approval through
   only if it names the draft it was shown (its fingerprint) and that draft
   was written from exactly the plan, comment and patient name being
   approved. The text is then stored on the approval.
3. `GET /report/{visit_id}` returns the stored text. It writes nothing and
   imports no LLM code (tests/test_report_wording.py).

So no sentence reaches a patient unless it was put in front of the approving
physician first, and every reader of a report sees the same sentences.
"""

import hashlib
import json
import logging
from concurrent.futures import ThreadPoolExecutor

from src.api.report_template import for_patient, template_report
from src.db.models import utcnow
from src.llm.client import (
    LLMIncompleteError,
    LLMNotConfiguredError,
    LLMRefusedError,
    LLMUnavailableError,
    llm_available,
)

log = logging.getLogger(__name__)

# a report can be read in either, whatever language the physician works in,
# so both are written and both are approved
LANGUAGES = ("en", "bn")


class WordingError(Exception):
    """An approval that does not match the wording prepared for it."""


def _digest(value) -> str:
    canonical = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def basis(source: str, lang: str, patient_name: str, result: dict, comment: str) -> str:
    """A digest of everything one wording is written from. Two wordings with
    the same basis say the same plan to the same patient; a draft whose basis
    is not that of the plan being approved describes some other plan. The
    template quotes the physician's comment, so its basis includes it; the
    LLM is never given the comment (the report shows it beside the text)."""
    written_from = {"source": source, "lang": lang, "patient_name": patient_name,
                    "result": for_patient(result)}
    if source == "template":
        written_from["comment"] = comment.strip()
    return _digest(written_from)


def _write(source: str, lang: str, patient_name: str, result: dict, comment: str) -> dict:
    """One language's wording. `fallback` says why the standard wording
    stands where the LLM's was asked for."""
    fallback = None
    if source == "llm":
        from src.llm.report_writer import write_report

        try:
            return {"text": write_report(patient_name, for_patient(result), lang),
                    "source": "llm", "fallback": None,
                    "basis": basis("llm", lang, patient_name, result, comment)}
        except LLMRefusedError as exc:
            fallback, reason = "refused", exc
        except LLMIncompleteError as exc:
            fallback, reason = "incomplete", exc
        except (LLMNotConfiguredError, LLMUnavailableError) as exc:
            fallback, reason = "unavailable", exc
        log.warning("report wording (%s) fell back to the template: %s", lang, reason)
    return {"text": template_report(patient_name, for_patient(result), lang, comment=comment),
            "source": "template", "fallback": fallback,
            "basis": basis("template", lang, patient_name, result, comment)}


def prepare(current: dict | None, patient_name: str, result: dict, comment: str,
            use_llm: bool, prepared_by: str) -> dict:
    """The report's wording in every language for the plan as it stands: the
    draft the physician reads before approving. `current` is the draft
    prepared before, if any: a wording it already holds for exactly these
    inputs is kept, so asking again writes nothing again (an LLM does not
    give the same sentences twice), and `current` itself is returned when
    nothing in it had to change."""
    source = "llm" if use_llm and llm_available() else "template"
    held = (current or {}).get("texts") or {}
    # a wording already held for exactly these inputs is kept. Its `fallback`
    # said why the standard wording stood in for the LLM's on an earlier
    # request; kept for this one, it is simply what was asked for (the LLM's,
    # or the standard wording with no LLM asked), so the reason goes
    kept = {
        lang: {**held[lang], "fallback": None} for lang in LANGUAGES
        if lang in held and held[lang]["source"] == source
        and held[lang]["basis"] == basis(source, lang, patient_name, result, comment)
    }
    missing = [lang for lang in LANGUAGES if lang not in kept]

    def write(lang: str) -> dict:
        return _write(source, lang, patient_name, result, comment)

    if source == "llm" and len(missing) > 1:
        # each language is one slow request: ask for them side by side
        with ThreadPoolExecutor(max_workers=len(missing)) as pool:
            written = dict(zip(missing, pool.map(write, missing)))
    else:
        written = {lang: write(lang) for lang in missing}
    texts = {lang: written.get(lang) or kept[lang] for lang in LANGUAGES}
    if current and texts == held:
        return current
    return {"fingerprint": _digest(texts), "texts": texts,
            "prepared_by": prepared_by, "prepared_at": utcnow().isoformat()}


def approved(draft: dict | None, shown: str | None, patient_name: str, result: dict,
             comment: str) -> dict:
    """The wording an approval releases: {lang: {"text", "source"}}, taken
    from the draft. Raises WordingError unless the approval names the draft
    (`shown`, the fingerprint the physician's screen was given with the
    text) and the draft was written from this plan, comment and name."""
    if not draft:
        raise WordingError(
            "Preview the report before approving: the patient reads the wording you were shown.")
    if shown != draft["fingerprint"]:
        raise WordingError(
            "The report was worded again after you read it. Preview the report again, then approve.")
    for lang, wording in draft["texts"].items():
        if wording["basis"] != basis(wording["source"], lang, patient_name, result, comment):
            raise WordingError(
                "The plan, your comment or the patient's name changed after the report was "
                "worded. Preview the report again, then approve.")
    return {lang: {"text": wording["text"], "source": wording["source"]}
            for lang, wording in draft["texts"].items()}


def provenance(draft: dict) -> dict:
    """What the audit log keeps of a wording: which text it was (not the text
    itself) and who or what wrote each language."""
    return {"fingerprint": draft["fingerprint"],
            "sources": {lang: wording["source"] for lang, wording in draft["texts"].items()}}

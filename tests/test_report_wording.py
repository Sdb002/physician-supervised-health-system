"""The patient reads the wording the physician approved.

A report's text is written before the decision (POST /review/{id}/wording),
returned to the physician to read, and stored with the approval. An approval
must name the wording it releases, and that wording must have been written
from the plan, comment and patient name being approved. GET /report/{visit_id}
serves the stored text: it writes none and imports no LLM code.

Part of guarantee 3 (no report without physician approval): an approval that
never saw its report's wording would not be an approval of what the patient
reads.
"""

import ast
import itertools
from pathlib import Path
from types import SimpleNamespace

import anthropic
import pytest
from sqlalchemy import select

from src.api.deps import get_db
from src.api.main import app
from src.db.models import Approval
from src.llm import report_writer
from src.llm.client import (
    LLMIncompleteError,
    LLMNotConfiguredError,
    LLMRefusedError,
    LLMUnavailableError,
)

SRC = Path(__file__).resolve().parents[1] / "src"

PATIENT = {"name": "Test Patient", "sex": "female", "birth_year": 1990, "height_cm": 160}
VISIT = {"weight_kg": 70, "biomarkers": {"fasting_glucose": 130, "systolic_bp": 150,
                                        "diastolic_bp": 95, "hemoglobin": 10.0}}
NO_AUTH = {"Authorization": ""}


def _pending(client) -> dict:
    patient_id = client.post("/patients", json=PATIENT).json()["id"]
    response = client.post(f"/patients/{patient_id}/visits", json=VISIT)
    assert response.status_code == 201
    return response.json()


def _word(client, assessment, **plan):
    return client.post(f"/review/{assessment['id']}/wording", json=plan)


def _decide(client, assessment, **decision):
    return client.post(f"/review/{assessment['id']}/decision",
                       json={"decision": "approved", **decision})


@pytest.fixture()
def ai(monkeypatch):
    """An LLM that is configured and answers. Every request made of it is
    kept, and no two answers are alike (as with a real one)."""
    requests, serial = [], itertools.count(1)

    def write_report(patient_name, result, lang):
        requests.append((patient_name, result, lang))
        return f"AI wording no. {next(serial)} ({lang}) for {patient_name}"

    monkeypatch.setattr("src.core.config.settings.anthropic_api_key", "test-key")
    monkeypatch.setattr(report_writer, "write_report", write_report)
    return requests


# --- the report route writes nothing ------------------------------------------

def test_the_report_route_imports_no_llm_code():
    """The route a patient's report comes from, and the standard wording it
    falls back on, cannot reach an LLM: neither imports one."""
    for module in ("api/routes/report.py", "api/report_template.py"):
        tree = ast.parse((SRC / module).read_text(encoding="utf-8"))
        imported = [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
                    for alias in node.names]
        imported += [node.module for node in ast.walk(tree)
                     if isinstance(node, ast.ImportFrom) and node.module]
        offenders = [name for name in imported
                     if name.split(".")[0] == "anthropic" or name.startswith("src.llm")
                     or name == "src.api.report_wording"]
        assert offenders == [], f"{module} imports {offenders}"


def test_the_wording_the_physician_was_shown_is_what_every_reader_gets(client, ai):
    assessment = _pending(client)
    assert assessment["result"]["cautions"], "the patient needs a note that is the physician's alone"

    shown = _word(client, assessment)
    assert shown.status_code == 200
    wording = shown.json()
    assert wording["ai_available"] is True
    assert {lang: text["source"] for lang, text in wording["texts"].items()} == {"en": "llm", "bn": "llm"}
    # written once per language, from the plan without the physician's cautions
    assert sorted(lang for _, _, lang in ai) == ["bn", "en"]
    assert all(name == "Test Patient" and "cautions" not in result and result["nutrition"]
               for name, result, _ in ai)

    # asking again for the same plan writes nothing again
    again = _word(client, assessment).json()
    assert again == wording and len(ai) == 2

    # nothing is released before the decision
    assert client.get(f"/report/{assessment['visit_id']}").status_code == 403
    assert _decide(client, assessment, wording=wording["fingerprint"]).status_code == 201

    for lang in ("en", "bn", "en"):
        report = client.get(f"/report/{assessment['visit_id']}?lang={lang}").json()
        assert report["text"] == wording["texts"][lang]["text"]
        assert report["source"] == "llm"

    # the patient reads the same sentences as the physician did
    patient_id = client.get(f"/review/{assessment['id']}").json()["patient"]["id"]
    client.post(f"/patients/{patient_id}/account",
                json={"email": "reader@test.local", "password": "password123"})
    token = client.post("/auth/login", headers=NO_AUTH, json={
        "email": "reader@test.local", "password": "password123"}).json()["token"]
    as_patient = client.get(f"/report/{assessment['visit_id']}?lang=bn",
                            headers={"Authorization": f"Bearer {token}"})
    assert as_patient.status_code == 200
    assert as_patient.json()["text"] == wording["texts"]["bn"]["text"]
    assert "cautions" not in as_patient.json()["result"]

    # opening the report, any number of times, asked the LLM for nothing
    assert len(ai) == 2


def test_no_approval_without_the_wording_it_releases(client):
    assessment = _pending(client)

    # never worded
    refused = _decide(client, assessment)
    assert refused.status_code == 409 and "Preview the report" in refused.json()["detail"]

    # worded, but the approval does not say which wording it read, or names another
    wording = _word(client, assessment).json()
    assert _decide(client, assessment).status_code == 409
    assert _decide(client, assessment, wording="0" * 64).status_code == 409

    # none of that decided anything
    assert client.get(f"/review/{assessment['id']}").json()["assessment"]["status"] == "pending"
    assert client.get(f"/report/{assessment['visit_id']}").status_code == 403

    assert _decide(client, assessment, wording=wording["fingerprint"]).status_code == 201


def test_a_rejection_needs_no_wording(client):
    assessment = _pending(client)
    rejected = client.post(f"/review/{assessment['id']}/decision", json={"decision": "rejected"})
    assert rejected.status_code == 201
    assert client.get(f"/report/{assessment['visit_id']}").status_code == 403
    # ...and a decided assessment is not worded again
    assert _word(client, assessment).status_code == 409


def test_a_wording_for_another_plan_or_comment_cannot_be_approved(client):
    assessment = _pending(client)
    edited = {**assessment["result"], "physician_note": "smaller dinner"}

    # the standard wording quotes the comment: written without it, it is not
    # the report of an approval that carries one
    plain = _word(client, assessment).json()
    with_comment = _decide(client, assessment, wording=plain["fingerprint"],
                           comment="Re-check haemoglobin in 4 weeks")
    assert with_comment.status_code == 409 and "changed after" in with_comment.json()["detail"]

    # worded for the engine's plan, approved with an edited one
    assert _decide(client, assessment, wording=plain["fingerprint"],
                   edited_result=edited).status_code == 409

    # worded for exactly what is approved
    final = _word(client, assessment, comment="Re-check haemoglobin in 4 weeks",
                  edited_result=edited).json()
    assert final["fingerprint"] != plain["fingerprint"]
    assert _decide(client, assessment, wording=final["fingerprint"],
                   comment="Re-check haemoglobin in 4 weeks",
                   edited_result=edited).status_code == 201
    report = client.get(f"/report/{assessment['visit_id']}").json()
    assert report["text"] == final["texts"]["en"]["text"]
    assert "A note from your physician: Re-check haemoglobin in 4 weeks" in report["text"]


def test_a_plan_rebuilt_after_the_wording_needs_a_new_one(client):
    assessment = _pending(client)
    wording = _word(client, assessment).json()
    patient_id = client.get(f"/review/{assessment['id']}").json()["patient"]["id"]

    # the record changes, so the pending plan is rebuilt from it
    client.patch(f"/patients/{patient_id}", json={"dietary_restrictions": ["vegetarian"]})
    stale = _decide(client, assessment, wording=wording["fingerprint"])
    assert stale.status_code == 409

    fresh = _word(client, assessment).json()
    assert fresh["fingerprint"] != wording["fingerprint"]
    assert _decide(client, assessment, wording=fresh["fingerprint"]).status_code == 201


def test_a_renamed_patient_needs_a_new_wording(client):
    assessment = _pending(client)
    wording = _word(client, assessment).json()
    assert "Dear Test Patient" in wording["texts"]["en"]["text"]
    patient_id = client.get(f"/review/{assessment['id']}").json()["patient"]["id"]
    client.patch(f"/patients/{patient_id}", json={"name": "Renamed Patient"})

    assert _decide(client, assessment, wording=wording["fingerprint"]).status_code == 409
    fresh = _word(client, assessment).json()
    assert "Dear Renamed Patient" in fresh["texts"]["en"]["text"]
    assert _decide(client, assessment, wording=fresh["fingerprint"]).status_code == 201


def test_a_wording_written_again_replaces_the_one_read_before(client, ai):
    assessment = _pending(client)
    by_ai = _word(client, assessment).json()
    # the physician asks for the standard wording instead (or someone else
    # words the report again): the earlier text is no longer what an approval releases
    standard = _word(client, assessment, use_llm=False).json()
    assert standard["fingerprint"] != by_ai["fingerprint"]
    assert {text["source"] for text in standard["texts"].values()} == {"template"}

    assert _decide(client, assessment, wording=by_ai["fingerprint"]).status_code == 409
    assert _decide(client, assessment, wording=standard["fingerprint"]).status_code == 201
    report = client.get(f"/report/{assessment['visit_id']}").json()
    assert report["source"] == "template" and "Dear Test Patient" in report["text"]


def test_with_the_llms_wording_a_comment_changes_nothing_it_wrote(client, ai):
    """The LLM is not given the comment (the report shows it beside the
    text), so adding one neither rewrites nor invalidates its wording."""
    assessment = _pending(client)
    wording = _word(client, assessment).json()
    with_comment = _word(client, assessment, comment="Walk after dinner").json()
    assert with_comment == wording and len(ai) == 2
    assert _decide(client, assessment, wording=wording["fingerprint"],
                   comment="Walk after dinner").status_code == 201
    report = client.get(f"/report/{assessment['visit_id']}").json()
    assert report["text"] == wording["texts"]["en"]["text"]
    assert report["comment"] == "Walk after dinner"


@pytest.mark.parametrize("failure, why", [
    (LLMRefusedError("declined"), "refused"),
    (LLMIncompleteError("cut off"), "incomplete"),
    (LLMUnavailableError("no answer"), "unavailable"),
    (LLMNotConfiguredError("no key"), "unavailable"),
])
def test_the_standard_wording_stands_in_when_the_llm_fails(client, monkeypatch, failure, why):
    def write_report(patient_name, result, lang):
        raise failure

    monkeypatch.setattr("src.core.config.settings.anthropic_api_key", "test-key")
    monkeypatch.setattr(report_writer, "write_report", write_report)
    assessment = _pending(client)
    wording = _word(client, assessment).json()
    for lang, greeting in (("en", "Dear Test Patient"), ("bn", "প্রিয় Test Patient")):
        text = wording["texts"][lang]
        assert text["source"] == "template" and text["fallback"] == why
        assert greeting in text["text"]
    # the physician is shown it like any other wording, and can approve it
    assert _decide(client, assessment, wording=wording["fingerprint"]).status_code == 201
    assert client.get(f"/report/{assessment['visit_id']}").json()["source"] == "template"


def test_a_failure_noted_on_an_earlier_wording_does_not_follow_the_standard_one(client, monkeypatch):
    """The Bangla AI wording fails, so the standard wording stands in, with
    the reason. Asked again for the standard wording on purpose, the same
    Bangla text is kept, but no longer as a stand-in for a failed AI."""
    def write_report(patient_name, result, lang):
        if lang == "bn":
            raise LLMUnavailableError("no answer")
        return f"AI wording ({lang})"

    monkeypatch.setattr("src.core.config.settings.anthropic_api_key", "test-key")
    monkeypatch.setattr(report_writer, "write_report", write_report)
    assessment = _pending(client)
    first = _word(client, assessment).json()
    assert first["texts"]["bn"]["fallback"] == "unavailable"

    standard = _word(client, assessment, use_llm=False).json()
    assert standard["texts"]["bn"]["text"] == first["texts"]["bn"]["text"]
    assert all(text["source"] == "template" and text["fallback"] is None
               for text in standard["texts"].values())
    assert standard["fingerprint"] != first["fingerprint"]
    # and with the key gone, the same: nothing about an AI that was not asked
    monkeypatch.setattr("src.core.config.settings.anthropic_api_key", "")
    without_key = _word(client, assessment).json()
    assert without_key["ai_available"] is False
    assert (without_key["fingerprint"], without_key["texts"]) == (standard["fingerprint"], standard["texts"])


def test_without_an_api_key_the_report_is_the_standard_wording(client, monkeypatch):
    monkeypatch.setattr("src.core.config.settings.anthropic_api_key", "")
    assessment = _pending(client)
    wording = _word(client, assessment).json()
    assert wording["ai_available"] is False
    assert all(text["source"] == "template" and text["fallback"] is None
               for text in wording["texts"].values())
    assert _decide(client, assessment, wording=wording["fingerprint"]).status_code == 201


def test_a_report_approved_before_wordings_were_kept_gets_the_standard_wording(client, ai):
    """Such an approval has no stored text. Its report is the deterministic
    wording of the approved plan; the LLM is not asked, configured or not."""
    assessment = _pending(client)
    wording = _word(client, assessment, use_llm=False).json()
    _decide(client, assessment, wording=wording["fingerprint"])

    db = next(app.dependency_overrides[get_db]())
    approval = db.scalars(select(Approval)).one()
    assert approval.report_text["en"]["text"] == wording["texts"]["en"]["text"]
    approval.report_text = None  # as migration 0006 leaves an earlier approval
    db.commit()
    db.close()

    report = client.get(f"/report/{assessment['visit_id']}?lang=bn").json()
    assert report["source"] == "template" and "প্রিয় Test Patient" in report["text"]
    assert ai == []


def test_the_audit_log_says_which_wording_was_released(client, ai):
    assessment = _pending(client)
    wording = _word(client, assessment).json()
    _word(client, assessment)  # unchanged: nothing new to record
    _decide(client, assessment, wording=wording["fingerprint"])

    trail = [entry for entry in client.get("/admin/audit?limit=50", headers=client.admin_headers).json()
             if entry["entity"] == "assessment" and entry["entity_id"] == assessment["id"]]
    worded = [entry for entry in trail if entry["action"] == "assessment.report_worded"]
    assert len(worded) == 1 and worded[0]["actor"] == "doctor@test.local"
    assert worded[0]["detail"] == {"fingerprint": wording["fingerprint"],
                                   "sources": {"en": "llm", "bn": "llm"}}
    approved = next(entry for entry in trail if entry["action"] == "assessment.approved")
    assert approved["detail"]["report"] == worded[0]["detail"]
    # the log keeps which text it was, not the text
    assert "AI wording" not in str(trail)


# --- the writer never passes off a failed reply as a report ---------------------

def _reply(text="Dear Test Patient, ...", stop_reason="end_turn"):
    content = [SimpleNamespace(type="thinking", thinking="")]
    if text is not None:
        content.append(SimpleNamespace(type="text", text=text))
    return SimpleNamespace(stop_reason=stop_reason, content=content)


def _sdk_error(kind, status_code=None):
    # built without the SDK's constructors, which want a live request object
    error = kind.__new__(kind)
    if status_code is not None:
        error.status_code = status_code
    return error


@pytest.mark.parametrize("outcome, expected", [
    (_reply(stop_reason="max_tokens"), LLMIncompleteError),
    (_reply(text=None), LLMIncompleteError),
    (_reply(text="   "), LLMIncompleteError),
    (_reply(stop_reason="refusal"), LLMRefusedError),
    (_sdk_error(anthropic.APIConnectionError), LLMUnavailableError),
    (_sdk_error(anthropic.APITimeoutError), LLMUnavailableError),
    (_sdk_error(anthropic.RateLimitError, 429), LLMUnavailableError),
    (_sdk_error(anthropic.APIStatusError, 529), LLMUnavailableError),
])
def test_the_writer_raises_rather_than_return_part_of_a_report(monkeypatch, outcome, expected):
    def create(**request):
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=create)))
    monkeypatch.setattr(report_writer, "get_client", lambda: client)
    with pytest.raises(expected):
        report_writer.write_report("Test Patient", {"nutrition": {}}, "en")


def test_the_writer_returns_the_reply_text(monkeypatch):
    seen = {}

    def create(**request):
        seen.update(request)
        return _reply("Dear Test Patient,\n\nYour plan...\n")

    client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=create)))
    monkeypatch.setattr(report_writer, "get_client", lambda: client)
    text = report_writer.write_report("Test Patient", {"nutrition": {"targets": {}}}, "bn")
    assert text == "Dear Test Patient,\n\nYour plan..."
    assert "Language: Bangla" in seen["messages"][0]["content"]

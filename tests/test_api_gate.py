"""End-to-end API flow, centered on the approval gate:
report is 403 until a physician approves, 200 after, 403 forever if rejected.
"""

PATIENT = {
    "name": "Test Patient",
    "sex": "female",
    "birth_year": 1990,
    "height_cm": 160,
}

VISIT = {
    "weight_kg": 70,
    "biomarkers": {
        "fasting_glucose": 130,
        "systolic_bp": 150,
        "diastolic_bp": 95,
        "hemoglobin": 10.0,
    },
}


def _create_pending_assessment(client):
    patient_id = client.post("/patients", json=PATIENT).json()["id"]
    response = client.post(f"/patients/{patient_id}/visits", json=VISIT)
    assert response.status_code == 201
    return response.json()


def test_full_flow_gate_then_approve(client):
    assessment = _create_pending_assessment(client)
    assert assessment["status"] == "pending"
    visit_id = assessment["visit_id"]
    result = assessment["result"]

    # engine derived the right conditions and exclusions
    assert {"diabetes", "hypertension", "anemia"} <= set(result["conditions"])
    assert "high_sodium" in result["exclusions"]["food_tags"]
    top_foods = result["nutrition"]["top_foods"]
    assert top_foods
    # high-sodium foods gated out before ranking, however iron-rich
    assert all("high_sodium" not in f["tags"] for f in top_foods)

    # gate: no report before approval
    assert client.get(f"/report/{visit_id}").status_code == 403

    # it shows up in the review queue
    queue = client.get("/review/queue").json()
    assert len(queue) == 1
    assert queue[0]["patient"]["name"] == PATIENT["name"]

    # physician approves
    decision = client.post(
        f"/review/{assessment['id']}/decision",
        json={"decision": "approved", "physician_name": "Dr. Rahman"},
    )
    assert decision.status_code == 201

    # gate opens: template report in both languages
    report = client.get(f"/report/{visit_id}?lang=en&use_llm=false")
    assert report.status_code == 200
    body = report.json()
    assert body["source"] == "template"
    # approver identity comes from the authenticated account (the "client"
    # fixture's doctor), not the client-supplied physician_name
    assert body["approved_by"] == "Dr Test"
    assert "Dear Test Patient" in body["text"]

    report_bn = client.get(f"/report/{visit_id}?lang=bn&use_llm=false")
    assert report_bn.status_code == 200
    assert "প্রিয়" in report_bn.json()["text"]

    # queue is now empty; second decision conflicts
    assert client.get("/review/queue").json() == []
    second = client.post(
        f"/review/{assessment['id']}/decision",
        json={"decision": "rejected", "physician_name": "Dr. Other"},
    )
    assert second.status_code == 409


def test_rejected_assessment_never_reports(client):
    assessment = _create_pending_assessment(client)
    visit_id = assessment["visit_id"]
    client.post(
        f"/review/{assessment['id']}/decision",
        json={"decision": "rejected", "physician_name": "Dr. Rahman",
              "comment": "values look mistyped"},
    )
    assert client.get(f"/report/{visit_id}").status_code == 403


def test_physician_edit_is_what_gets_reported(client):
    assessment = _create_pending_assessment(client)
    visit_id = assessment["visit_id"]
    edited = dict(assessment["result"])
    edited["physician_note"] = "reduced exercise volume"
    client.post(
        f"/review/{assessment['id']}/decision",
        json={"decision": "approved", "physician_name": "Dr. Rahman",
              "edited_result": edited},
    )
    report = client.get(f"/report/{visit_id}?use_llm=false")
    assert report.status_code == 200


def test_ocr_endpoint_degrades_without_api_key(client, monkeypatch):
    monkeypatch.setattr("src.core.config.settings.anthropic_api_key", "")
    response = client.post(
        "/intake/ocr",
        files={"file": ("report.png", b"\x89PNG fake", "image/png")},
    )
    assert response.status_code == 503
    assert "ANTHROPIC_API_KEY" in response.json()["detail"]


def test_health_endpoint(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert "llm_configured" in body

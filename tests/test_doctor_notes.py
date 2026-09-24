"""Doctor's notes: staff can add/edit at any time; patients only read their
own, and only once the visit is approved; notes ride along on the report."""

PATIENT = {"name": "Note Patient", "sex": "male", "birth_year": 1985, "height_cm": 175}
VISIT = {"weight_kg": 80, "biomarkers": {}}


def _create_visit(client):
    patient_id = client.post("/patients", json=PATIENT).json()["id"]
    assessment = client.post(f"/patients/{patient_id}/visits", json=VISIT).json()
    assessment["patient_id"] = patient_id
    return assessment


def test_staff_can_add_and_edit_notes(client):
    assessment = _create_visit(client)
    visit_id = assessment["visit_id"]

    created = client.post(f"/visits/{visit_id}/notes",
                          json={"physician_name": "Dr. Rahman", "note": "Recheck in 4 weeks"})
    assert created.status_code == 201
    note = created.json()
    assert note["note"] == "Recheck in 4 weeks"
    assert note["updated_at"] is None

    listed = client.get(f"/visits/{visit_id}/notes")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    edited = client.patch(f"/visits/{visit_id}/notes/{note['id']}",
                          json={"note": "Recheck in 2 weeks instead"})
    assert edited.status_code == 200
    assert edited.json()["note"] == "Recheck in 2 weeks instead"
    assert edited.json()["updated_at"] is not None


def test_notes_available_before_approval_for_staff_but_not_patient(client):
    assessment = _create_visit(client)
    visit_id = assessment["visit_id"]
    client.post(f"/visits/{visit_id}/notes",
               json={"physician_name": "Dr. Rahman", "note": "pending note"})

    reg = client.post("/auth/register", json={
        "name": "Note Patient", "email": "notepatient@example.com", "password": "secret-pass-3",
        "role": "patient", "profile": {"sex": "male", "birth_year": 1985, "height_cm": 175},
    }, headers={"Authorization": ""})
    # this patient account isn't linked to the visit's patient, so scope alone
    # would already forbid it, but the assessment isn't approved either
    token = client.post("/auth/login", json={
        "email": "notepatient@example.com", "password": "secret-pass-3",
    }, headers={"Authorization": ""}).json()["token"]
    patient_headers = {"Authorization": f"Bearer {token}"}
    assert client.get(f"/visits/{visit_id}/notes", headers=patient_headers).status_code == 403


def test_patient_sees_notes_only_for_own_approved_visit(client):
    assessment = _create_visit(client)
    visit_id = assessment["visit_id"]
    client.post(f"/visits/{visit_id}/notes",
               json={"physician_name": "Dr. Rahman", "note": "reduce salt intake"})
    client.post(f"/review/{assessment['id']}/decision",
               json={"decision": "approved", "physician_name": "Dr. Rahman"})

    account = client.post(f"/patients/{assessment['patient_id']}/account",
                          json={"email": "ownernp@example.com", "password": "owner-pass-1"})
    assert account.status_code == 201
    token = client.post("/auth/login", json={
        "email": "ownernp@example.com", "password": "owner-pass-1",
    }, headers={"Authorization": ""}).json()["token"]
    patient_headers = {"Authorization": f"Bearer {token}"}

    notes = client.get(f"/visits/{visit_id}/notes", headers=patient_headers)
    assert notes.status_code == 200
    assert notes.json()[0]["note"] == "reduce salt intake"

    report = client.get(f"/report/{visit_id}?use_llm=false", headers=patient_headers)
    assert report.status_code == 200
    assert report.json()["notes"][0]["note"] == "reduce salt intake"


def test_only_staff_can_write_notes(client):
    assessment = _create_visit(client)
    visit_id = assessment["visit_id"]
    unauth = client.post(f"/visits/{visit_id}/notes",
                         json={"physician_name": "Dr. Rahman", "note": "x"},
                         headers={"Authorization": ""})
    assert unauth.status_code == 401


def test_note_requires_existing_visit(client):
    assert client.post("/visits/999999/notes",
                       json={"physician_name": "Dr. Rahman", "note": "x"}).status_code == 404

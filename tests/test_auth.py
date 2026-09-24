"""Auth + roles: doctor approval flow, route protection, patient report scope."""

NO_AUTH = {"Authorization": ""}

DOCTOR_REG = {
    "name": "Dr Nadia Islam",
    "email": "nadia@example.com",
    "password": "secret-pass-1",
    "role": "doctor",
    "specialty": "Endocrinology",
    "license_no": "BMDC-12345",
}

PATIENT_REG = {
    "name": "Rahim Uddin",
    "email": "rahim@example.com",
    "password": "secret-pass-2",
    "role": "patient",
    "profile": {"sex": "male", "birth_year": 1988, "height_cm": 170},
}


def test_workflow_routes_require_staff_auth(client):
    assert client.get("/patients", headers=NO_AUTH).status_code == 401
    assert client.get("/review/queue", headers=NO_AUTH).status_code == 401
    assert client.get("/report/1", headers=NO_AUTH).status_code == 401


def test_doctor_registration_needs_admin_approval(client):
    # register → pending, login blocked with a clear message
    created = client.post("/auth/register", json=DOCTOR_REG, headers=NO_AUTH)
    assert created.status_code == 201
    assert created.json()["status"] == "pending"

    login = client.post("/auth/login", json={"email": DOCTOR_REG["email"],
                                             "password": DOCTOR_REG["password"]},
                        headers=NO_AUTH)
    assert login.status_code == 403
    assert "awaiting admin approval" in login.json()["detail"]

    # a plain doctor cannot approve; the admin can
    doctor_id = created.json()["id"]
    assert client.post(f"/admin/doctors/{doctor_id}/decision",
                       json={"decision": "approved"}).status_code == 403
    approved = client.post(f"/admin/doctors/{doctor_id}/decision",
                           json={"decision": "approved"}, headers=client.admin_headers)
    assert approved.status_code == 200
    assert approved.json()["status"] == "active"

    # now login works and the token reaches staff routes
    login = client.post("/auth/login", json={"email": DOCTOR_REG["email"],
                                             "password": DOCTOR_REG["password"]},
                        headers=NO_AUTH)
    assert login.status_code == 200
    token = login.json()["token"]
    queue = client.get("/review/queue", headers={"Authorization": f"Bearer {token}"})
    assert queue.status_code == 200


def test_rejected_doctor_cannot_login(client):
    reg = {**DOCTOR_REG, "email": "other@example.com"}
    doctor_id = client.post("/auth/register", json=reg, headers=NO_AUTH).json()["id"]
    client.post(f"/admin/doctors/{doctor_id}/decision",
                json={"decision": "rejected"}, headers=client.admin_headers)
    login = client.post("/auth/login", json={"email": reg["email"],
                                             "password": reg["password"]},
                        headers=NO_AUTH)
    assert login.status_code == 403
    assert "declined" in login.json()["detail"]


def test_role_scoped_login_page(client):
    client.post("/auth/register", json=PATIENT_REG, headers=NO_AUTH)
    # patient credentials on the doctor sign-in page are refused
    wrong_portal = client.post("/auth/login", json={"email": PATIENT_REG["email"],
                                                    "password": PATIENT_REG["password"],
                                                    "role": "doctor"},
                               headers=NO_AUTH)
    assert wrong_portal.status_code == 403


def test_patient_sees_only_own_visits_and_reports(client):
    # patient registers → active immediately, linked Patient row, empty dashboard
    reg = client.post("/auth/register", json=PATIENT_REG, headers=NO_AUTH).json()
    assert reg["status"] == "active"
    assert reg["patient_id"] is not None
    token = client.post("/auth/login", json={"email": PATIENT_REG["email"],
                                             "password": PATIENT_REG["password"]},
                        headers=NO_AUTH).json()["token"]
    patient_headers = {"Authorization": f"Bearer {token}"}

    dash = client.get("/me/dashboard", headers=patient_headers)
    assert dash.status_code == 200
    assert dash.json()["items"] == []

    # the doctor records a visit for a DIFFERENT patient and approves it
    other_id = client.post("/patients", json={"name": "Someone Else", "sex": "female",
                                              "birth_year": 1990, "height_cm": 160}).json()["id"]
    assessment = client.post(f"/patients/{other_id}/visits",
                             json={"weight_kg": 60, "biomarkers": {}}).json()
    client.post(f"/review/{assessment['id']}/decision",
                json={"decision": "approved", "physician_name": "Dr Test"})
    other_visit = assessment["visit_id"]

    # the patient cannot read someone else's approved report; staff can
    assert client.get(f"/report/{other_visit}?use_llm=false",
                      headers=patient_headers).status_code == 403
    assert client.get(f"/report/{other_visit}?use_llm=false").status_code == 200

    # patients cannot reach staff routes
    assert client.get("/patients", headers=patient_headers).status_code == 403
    assert client.get("/admin/stats", headers=patient_headers).status_code == 403


def test_doctor_creates_patient_login(client):
    # doctor registers a walk-in patient, then sets up their login
    patient_id = client.post("/patients", json={"name": "Walk In", "sex": "male",
                                                "birth_year": 1975, "height_cm": 168}).json()["id"]
    assert client.get(f"/patients/{patient_id}/account").json() == {"email": None}

    created = client.post(f"/patients/{patient_id}/account",
                          json={"email": "walkin@example.com", "password": "walkin-pass-1"})
    assert created.status_code == 201
    assert created.json()["role"] == "patient"
    assert created.json()["patient_id"] == patient_id
    assert client.get(f"/patients/{patient_id}/account").json() == {"email": "walkin@example.com"}

    # the patient can sign in immediately and sees their (empty) dashboard
    login = client.post("/auth/login", json={"email": "walkin@example.com",
                                             "password": "walkin-pass-1"}, headers=NO_AUTH)
    assert login.status_code == 200
    dash = client.get("/me/dashboard",
                      headers={"Authorization": f"Bearer {login.json()['token']}"})
    assert dash.status_code == 200
    assert dash.json()["patient"]["name"] == "Walk In"

    # one login per patient; duplicate emails rejected
    assert client.post(f"/patients/{patient_id}/account",
                       json={"email": "x@example.com", "password": "password123"}).status_code == 409


def test_admin_patient_list_shows_linked_accounts(client):
    client.post("/auth/register", json=PATIENT_REG, headers=NO_AUTH)
    client.post("/patients", json={"name": "No Login", "sex": "female",
                                   "birth_year": 1992, "height_cm": 155})

    # admin-only
    assert client.get("/admin/patients").status_code == 403
    rows = client.get("/admin/patients", headers=client.admin_headers)
    assert rows.status_code == 200
    by_name = {r["patient"]["name"]: r["account_email"] for r in rows.json()}
    assert by_name["Rahim Uddin"] == "rahim@example.com"
    assert by_name["No Login"] is None


def test_duplicate_email_rejected(client):
    assert client.post("/auth/register", json=PATIENT_REG, headers=NO_AUTH).status_code == 201
    assert client.post("/auth/register", json=PATIENT_REG, headers=NO_AUTH).status_code == 409

"""A patient belongs to one doctor. Another doctor cannot open the patient or
anything recorded for them; an admin can, and is the only one who can move a
patient between doctors (src/api/access.py)."""

from sqlalchemy import create_engine, text

from alembic import command
from src.db.session import init_db, migration_config

NO_AUTH = {"Authorization": ""}
PATIENT = {"name": "Ayesha Rahman", "sex": "female", "birth_year": 1990, "height_cm": 158}
VISIT = {"weight_kg": 60, "biomarkers": {"fasting_glucose": 130, "hemoglobin": 10.5}}
SELF_REGISTERED = {
    "name": "Karim Hossain", "email": "karim@test.local", "password": "password123",
    "role": "patient",
    "profile": {"sex": "male", "birth_year": 1985, "height_cm": 170},
}


def _other_doctor(client) -> dict:
    """A second active doctor, registered and approved the way a real one is."""
    reg = client.post("/auth/register", headers=NO_AUTH, json={
        "name": "Dr Other", "email": "other@test.local", "password": "password123",
        "role": "doctor", "specialty": "Medicine", "license_no": "A-2"}).json()
    client.post(f"/admin/doctors/{reg['id']}/decision", json={"decision": "approved"},
                headers=client.admin_headers)
    token = client.post("/auth/login", headers=NO_AUTH, json={
        "email": "other@test.local", "password": "password123"}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def _patient_with_approved_visit(client) -> tuple[int, int, int]:
    patient_id = client.post("/patients", json=PATIENT).json()["id"]
    assessment = client.post(f"/patients/{patient_id}/visits", json=VISIT).json()
    client.approve(assessment["id"])
    return patient_id, assessment["visit_id"], assessment["id"]


def test_a_new_patient_belongs_to_the_doctor_who_registered_them(client):
    patient = client.post("/patients", json=PATIENT).json()
    doctors = {u["email"]: u["id"] for u in client.get("/admin/users", headers=client.admin_headers).json()}
    assert patient["doctor_id"] == doctors["doctor@test.local"]
    assert [p["id"] for p in client.get("/patients").json()] == [patient["id"]]


def test_another_doctor_sees_none_of_a_patients_records(client):
    patient_id, visit_id, assessment_id = _patient_with_approved_visit(client)
    pending = client.post(f"/patients/{patient_id}/visits", json=VISIT).json()["id"]
    note = client.post(f"/visits/{visit_id}/notes", json={"note": "walk daily"}).json()["id"]
    other = _other_doctor(client)

    assert client.get("/patients", headers=other).json() == []
    assert client.get("/review/queue", headers=other).json() == []
    # the same answer as for a patient who does not exist
    assert client.get("/patients/9999", headers=other).status_code == 404
    reads = [
        f"/patients/{patient_id}", f"/patients/{patient_id}/visits", f"/patients/{patient_id}/account",
        f"/review/{assessment_id}", f"/review/{pending}/foods",
        f"/report/{visit_id}", f"/visits/{visit_id}/notes",
    ]
    for url in reads:
        assert client.get(url, headers=other).status_code == 404, url
    writes = [
        ("patch", f"/patients/{patient_id}", {"notes": "mine now"}),
        ("post", f"/patients/{patient_id}/visits", VISIT),
        ("post", f"/patients/{patient_id}/account", {"email": "x@test.local", "password": "password123"}),
        ("post", f"/patients/{patient_id}/claim", None),
        ("post", f"/review/{pending}/wording", {}),
        ("post", f"/review/{pending}/decision", {"decision": "approved"}),
        ("post", f"/review/{pending}/recompute", {"meals": {}}),
        ("post", f"/visits/{visit_id}/notes", {"note": "not my patient"}),
        ("patch", f"/visits/{visit_id}/notes/{note}", {"note": "rewritten"}),
    ]
    for method, url, body in writes:
        assert getattr(client, method)(url, json=body, headers=other).status_code == 404, url

    # nothing the other doctor tried took effect, and the patient's own doctor reads it all
    assert client.get(f"/patients/{patient_id}").json()["notes"] == ""
    assert client.get(f"/review/{pending}").json()["assessment"]["status"] == "pending"
    assert client.get(f"/visits/{visit_id}/notes").json()[0]["note"] == "walk daily"
    assert client.get(f"/report/{visit_id}").status_code == 200


def test_each_doctor_reviews_only_their_own_queue(client):
    mine = client.post("/patients", json=PATIENT).json()["id"]
    my_assessment = client.post(f"/patients/{mine}/visits", json=VISIT).json()["id"]
    other = _other_doctor(client)
    theirs = client.post("/patients", json={**PATIENT, "name": "Theirs"}, headers=other).json()["id"]
    their_assessment = client.post(f"/patients/{theirs}/visits", json=VISIT, headers=other).json()["id"]

    assert [q["assessment"]["id"] for q in client.get("/review/queue").json()] == [my_assessment]
    assert [q["assessment"]["id"]
            for q in client.get("/review/queue", headers=other).json()] == [their_assessment]


def test_a_self_registered_patient_has_no_doctor_until_one_takes_them_on(client):
    reg = client.post("/auth/register", json=SELF_REGISTERED, headers=NO_AUTH).json()
    patient_id = reg["patient_id"]
    other = _other_doctor(client)

    # listed for doctors by name, sex and year of birth only
    listed = client.get("/patients/unassigned").json()
    assert [p["id"] for p in listed] == [patient_id]
    assert set(listed[0]) == {"id", "name", "sex", "birth_year", "created_at"}
    # the record itself stays closed until a doctor takes the patient on
    assert client.get(f"/patients/{patient_id}").status_code == 404
    assert client.post(f"/patients/{patient_id}/visits", json=VISIT).status_code == 404

    claimed = client.post(f"/patients/{patient_id}/claim")
    assert claimed.status_code == 200 and claimed.json()["doctor_id"] is not None
    assert client.get("/patients/unassigned").json() == []
    assert client.post(f"/patients/{patient_id}/visits", json=VISIT).status_code == 201
    # taking on one's own patient again changes nothing; another doctor cannot take them
    assert client.post(f"/patients/{patient_id}/claim").status_code == 200
    assert client.post(f"/patients/{patient_id}/claim", headers=other).status_code == 404
    assert client.get(f"/patients/{patient_id}", headers=other).status_code == 404

    actions = [a["action"] for a in client.get("/admin/audit", headers=client.admin_headers).json()]
    assert actions.count("patient.claim") == 1


def test_an_admin_reaches_every_patient_and_moves_them_between_doctors(client):
    patient_id, visit_id, _ = _patient_with_approved_visit(client)
    other = _other_doctor(client)
    admin = client.admin_headers
    other_id = next(u["id"] for u in client.get("/admin/users", headers=admin).json()
                    if u["email"] == "other@test.local")

    assert client.get(f"/patients/{patient_id}", headers=admin).status_code == 200
    assert client.get(f"/report/{visit_id}", headers=admin).status_code == 200
    # an admin does not take patients on, and only an admin assigns them
    assert client.post(f"/patients/{patient_id}/claim", headers=admin).status_code == 403
    assert client.patch(f"/admin/patients/{patient_id}/doctor",
                        json={"doctor_id": other_id}).status_code == 403
    # not to a patient account, a pending doctor or nobody's id
    assert client.patch(f"/admin/patients/{patient_id}/doctor", json={"doctor_id": 9999},
                        headers=admin).status_code == 422

    moved = client.patch(f"/admin/patients/{patient_id}/doctor", json={"doctor_id": other_id},
                         headers=admin)
    assert moved.status_code == 200 and moved.json()["doctor_id"] == other_id
    assert client.get(f"/patients/{patient_id}").status_code == 404
    assert client.get(f"/patients/{patient_id}", headers=other).status_code == 200
    assert client.get(f"/report/{visit_id}", headers=other).status_code == 200

    released = client.patch(f"/admin/patients/{patient_id}/doctor", json={"doctor_id": None},
                            headers=admin)
    assert released.json()["doctor_id"] is None
    assert [p["id"] for p in client.get("/patients/unassigned").json()] == [patient_id]


def test_a_patient_still_reads_their_own_report_whoever_their_doctor_is(client):
    reg = client.post("/auth/register", json=SELF_REGISTERED, headers=NO_AUTH).json()
    token = client.post("/auth/login", headers=NO_AUTH, json={
        "email": SELF_REGISTERED["email"], "password": SELF_REGISTERED["password"]}).json()["token"]
    patient = {"Authorization": f"Bearer {token}"}
    client.post(f"/patients/{reg['patient_id']}/claim")
    assessment = client.post(f"/patients/{reg['patient_id']}/visits", json=VISIT).json()
    client.approve(assessment["id"])

    assert client.get(f"/report/{assessment['visit_id']}", headers=patient).status_code == 200
    assert client.get("/patients/unassigned", headers=patient).status_code == 403


def test_the_migration_reads_each_patients_doctor_off_the_audit_log(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'app.db').as_posix()}")
    command.upgrade(migration_config(engine), "0004")
    now = "'2026-01-01 00:00:00'"
    with engine.begin() as c:
        for uid, email, role in [(1, "a@x", "doctor"), (2, "b@x", "doctor"), (3, "admin@x", "admin")]:
            c.execute(text(
                "INSERT INTO users (id, email, password_hash, name, role, status, specialty, license_no, "
                f"created_at) VALUES ({uid}, '{email}', 'x', 'n', '{role}', 'active', '', '', {now})"))
        for pid in (1, 2, 3, 4):
            c.execute(text(
                "INSERT INTO patients (id, name, sex, birth_year, height_cm, pregnant, conditions, "
                "dietary_restrictions, excluded_foods, fitness_level, notes, created_at) VALUES "
                f"({pid}, 'p', 'female', 1990, 158, 0, '[]', '[]', '[]', 'beginner', '', {now})"))
            c.execute(text(f"INSERT INTO visits (id, patient_id, weight_kg, biomarkers, created_at) "
                           f"VALUES ({pid}, {pid}, 60, '{{}}', {now})"))
            c.execute(text("INSERT INTO assessments (id, visit_id, result, engine_version, status, created_at) "
                           f"VALUES ({pid}, {pid}, '{{}}', '0.13.0', 'pending', {now})"))
        log = ("INSERT INTO audit_log (actor, action, entity, entity_id, detail, created_at) "
               "VALUES ('{actor}', '{action}', '{entity}', {id}, '{{}}', " + now + ")")
        # patient 1: decided by doctor a, later edited by doctor b - the first decision counts
        c.execute(text(log.format(actor="a@x", action="assessment.approved", entity="assessment", id=1)))
        c.execute(text(log.format(actor="b@x", action="patient.update", entity="patient", id=1)))
        # patient 2: only ever edited, by doctor b
        c.execute(text(log.format(actor="b@x", action="patient.update", entity="patient", id=2)))
        # patient 3: decided by an admin, who is not a doctor; patient 4: untouched
        c.execute(text(log.format(actor="admin@x", action="assessment.approved", entity="assessment", id=3)))

    init_db(engine)

    with engine.connect() as c:
        doctors = dict(c.execute(text("SELECT id, doctor_id FROM patients ORDER BY id")).all())
    assert doctors == {1: 1, 2: 2, 3: None, 4: None}

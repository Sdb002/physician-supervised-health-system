"""The synthetic demo patients and demo logins.

Seeded by scripts/seed_db.py on a developer's machine, and by the API at
start-up when SEED_DEMO_DATA is set (a hosted demo, whose database starts
empty and whose password nobody needs to hand out). Either way only into a
database with no patients yet, so it runs once.

All patients here are synthetic (tests/fixtures/synthetic_patients.json).
The demo passwords are published in the README: a deployment that seeds them
lets anyone with its address sign in as the demo doctor and demo patient.
"""

import copy
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core import audit
from src.core.security import hash_password
from src.db.models import Assessment, Patient, User, Visit

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "synthetic_patients.json"

# demo login accounts (password shown next to each) — the admin account is
# created by the API itself at startup (see ADMIN_* in .env)
DEMO_USERS = [
    dict(email="doctor@health.local", password="doctor12345", name="Dr. Demo Physician",
         role="doctor", status="active", specialty="Internal Medicine",
         license_no="BMDC-00001"),
    dict(email="pending.doctor@health.local", password="doctor12345", name="Dr. Awaiting Approval",
         role="doctor", status="pending", specialty="Cardiology",
         license_no="BMDC-00002"),
]
DEMO_PATIENT_LOGIN = ("patient@health.local", "patient12345")


def seed_demo(db: Session, actor: str = "seed_db", report=print) -> bool:
    """Add the demo patients, each with one visit awaiting review, and the
    demo logins, in one transaction. Returns False, and adds nothing, when
    the database already has patients. Two of these running at once (two
    API instances starting together) cannot both succeed: the second
    stops on the demo logins' unique emails and rolls back whole."""
    # imported here: the engine pulls in the food tables and the models
    from src.api.services import ENGINE_VERSION, build_assessment

    if db.scalars(select(Patient)).first() is not None:
        return False

    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    first_patient_user: User | None = None
    for entry in copy.deepcopy(fixtures):
        visit_data = entry.pop("visit")
        patient = Patient(**entry)
        db.add(patient)
        db.flush()

        visit = Visit(patient_id=patient.id, weight_kg=visit_data["weight_kg"],
                      biomarkers=visit_data["biomarkers"])
        db.add(visit)
        db.flush()

        result = build_assessment(patient, visit)
        db.add(Assessment(visit_id=visit.id, result=result, engine_version=ENGINE_VERSION))
        audit.record(db, actor=actor, action="patient.seed", entity="patient", entity_id=patient.id)
        report(f"seeded {patient.name}: risk={result['overall_risk']}, "
               f"conditions={result['conditions']}")

        # give the first seeded patient a login so the patient dashboard
        # is demonstrable out of the box
        if first_patient_user is None:
            email, password = DEMO_PATIENT_LOGIN
            first_patient_user = User(email=email, password_hash=hash_password(password),
                                      name=patient.name, role="patient", status="active",
                                      patient_id=patient.id)
            db.add(first_patient_user)
            report(f"  ↳ login: {email} / {password} ({patient.name})")

    for demo in DEMO_USERS:
        fields = dict(demo)
        password = fields.pop("password")
        db.add(User(password_hash=hash_password(password), **fields))
        report(f"seeded user {fields['email']} / {password} ({fields['role']}, {fields['status']})")
    db.flush()
    # a doctor sees only their own patients: the demo ones are the demo doctor's
    demo_doctor = db.scalars(select(User).where(User.email == "doctor@health.local")).one()
    for patient in db.scalars(select(Patient)):
        patient.doctor_id = demo_doctor.id
    db.commit()
    report(f"done — {len(fixtures)} patients with pending assessments")
    return True

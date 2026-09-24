"""Create the database and seed it with the synthetic demo patients.

Run from the project root:  .venv\\Scripts\\python.exe scripts\\seed_db.py
Each seeded patient gets one visit with a pending assessment, ready for the
review queue in the dashboard.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select  # noqa: E402

from src.api.services import ENGINE_VERSION, build_assessment  # noqa: E402
from src.core import audit  # noqa: E402
from src.core.security import hash_password  # noqa: E402
from src.db.models import Assessment, Patient, User, Visit  # noqa: E402
from src.db.session import SessionLocal, init_db  # noqa: E402

FIXTURES = PROJECT_ROOT / "tests" / "fixtures" / "synthetic_patients.json"

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


def main() -> None:
    init_db()
    with SessionLocal() as db:
        if db.scalars(select(Patient)).first() is not None:
            print("database already has patients — nothing to do")
            return

        fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
        first_patient_user: User | None = None
        for entry in fixtures:
            visit_data = entry.pop("visit")
            patient = Patient(**entry)
            db.add(patient)
            db.flush()

            visit = Visit(
                patient_id=patient.id,
                weight_kg=visit_data["weight_kg"],
                biomarkers=visit_data["biomarkers"],
            )
            db.add(visit)
            db.flush()

            result = build_assessment(patient, visit)
            db.add(Assessment(visit_id=visit.id, result=result, engine_version=ENGINE_VERSION))
            audit.record(db, actor="seed_db", action="patient.seed",
                         entity="patient", entity_id=patient.id)
            print(f"seeded {patient.name}: risk={result['overall_risk']}, "
                  f"conditions={result['conditions']}")

            # give the first seeded patient a login so the patient dashboard
            # is demonstrable out of the box
            if first_patient_user is None:
                first_patient_user = User(
                    email="patient@health.local",
                    password_hash=hash_password("patient12345"),
                    name=patient.name, role="patient", status="active",
                    patient_id=patient.id,
                )
                db.add(first_patient_user)
                print(f"  ↳ login: patient@health.local / patient12345 ({patient.name})")

        for demo in DEMO_USERS:
            password = demo.pop("password")
            db.add(User(password_hash=hash_password(password), **demo))
            print(f"seeded user {demo['email']} / {password} "
                  f"({demo['role']}, {demo['status']})")
        db.commit()
    print(f"done — {len(fixtures)} patients with pending assessments")


if __name__ == "__main__":
    main()

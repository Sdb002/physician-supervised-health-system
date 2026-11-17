from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.access import own_patients, patient_for
from src.api.deps import get_db, require_staff
from src.api.schemas import (
    PatientAccountCreate,
    PatientAccountOut,
    PatientCreate,
    PatientOut,
    PatientUpdate,
    UnassignedPatientOut,
    UserOut,
    VisitOut,
)
from src.api.services import ENGINE_VERSION, build_assessment, excluded_food_entries
from src.core import audit
from src.core.security import hash_password
from src.db.models import Assessment, Patient, User, Visit

router = APIRouter(prefix="/patients", tags=["patients"])

_CLEARABLE = {"pregnancy_trimester", "activity_level"}


def _excluded_foods(chosen: list, kept: list[dict] | None = None) -> list[dict]:
    """What a form sent as the entries a patient keeps; 422 for an id that
    is neither a food nor a dish."""
    try:
        return excluded_food_entries(chosen, kept)
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@router.post("", response_model=PatientOut, status_code=201)
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    staff: User = Depends(require_staff),
):
    """A doctor's new patient is theirs. One an admin registers has no doctor
    until the admin assigns one."""
    fields = payload.model_dump()
    fields["excluded_foods"] = _excluded_foods(payload.excluded_foods)
    patient = Patient(**fields, doctor_id=staff.id if staff.role == "doctor" else None)
    db.add(patient)
    db.flush()
    audit.record(db, actor=staff.email, action="patient.create", entity="patient",
                 entity_id=patient.id, detail={"doctor_id": patient.doctor_id})
    db.commit()
    return patient


@router.get("", response_model=list[PatientOut])
def list_patients(db: Session = Depends(get_db), staff: User = Depends(require_staff)):
    """A doctor's own patients; every patient for an admin."""
    return list(db.scalars(own_patients(select(Patient), staff).order_by(Patient.id.desc())))


@router.get("/unassigned", response_model=list[UnassignedPatientOut])
def list_unassigned_patients(db: Session = Depends(get_db)):
    """Patients no doctor has yet: people who registered themselves. Name, sex
    and year of birth only, so a doctor can find the person at their desk
    without reading anyone's record."""
    return list(db.scalars(
        select(Patient).where(Patient.doctor_id.is_(None)).order_by(Patient.id.desc())
    ))


@router.post("/{patient_id}/claim", response_model=PatientOut)
def claim_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    staff: User = Depends(require_staff),
):
    """A doctor takes on a patient who has no doctor. A patient who already
    has one can only be moved by an admin."""
    if staff.role != "doctor":
        raise HTTPException(403, "only a doctor can take on a patient")
    patient = db.get(Patient, patient_id)
    if patient is None or patient.doctor_id not in (None, staff.id):
        raise HTTPException(404, "patient not found")
    if patient.doctor_id is None:
        patient.doctor_id = staff.id
        audit.record(db, actor=staff.email, action="patient.claim", entity="patient",
                     entity_id=patient.id, detail={"doctor_id": staff.id})
        db.commit()
    return patient


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db), staff: User = Depends(require_staff)):
    return patient_for(staff, patient_id, db)


@router.patch("/{patient_id}", response_model=PatientOut)
def update_patient(
    patient_id: int,
    payload: PatientUpdate,
    db: Session = Depends(get_db),
    staff: User = Depends(require_staff),
):
    """Change a patient's record. A plan still awaiting review was built from
    the old record, so it is rebuilt from the new one; approved and rejected
    assessments stay exactly as they were signed off."""
    patient = patient_for(staff, patient_id, db)
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("excluded_foods") is not None:
        changes["excluded_foods"] = _excluded_foods(payload.excluded_foods,
                                                    kept=patient.excluded_foods)
    for field, value in changes.items():
        # only the trimester and the activity level can be cleared
        if value is None and field not in _CLEARABLE:
            continue
        setattr(patient, field, value)
    if not patient.pregnant:
        patient.pregnancy_trimester = None
    db.flush()

    rebuilt = []
    pending = db.scalars(
        select(Assessment).join(Visit).where(
            Visit.patient_id == patient.id, Assessment.status == "pending")
    )
    for assessment in pending:
        assessment.result = build_assessment(patient, assessment.visit)
        assessment.engine_version = ENGINE_VERSION
        # a report worded for the old plan cannot be approved with the new one
        assessment.report_draft = None
        rebuilt.append(assessment.id)
    audit.record(db, actor=staff.email, action="patient.update", entity="patient",
                 entity_id=patient.id,
                 detail={"fields": sorted(changes), "assessments_rebuilt": rebuilt})
    db.commit()
    return patient


@router.get("/{patient_id}/account", response_model=PatientAccountOut)
def get_patient_account(
    patient_id: int, db: Session = Depends(get_db), staff: User = Depends(require_staff)
):
    patient_for(staff, patient_id, db)
    user = db.scalars(select(User).where(User.patient_id == patient_id)).first()
    return PatientAccountOut(email=user.email if user else None)


@router.post("/{patient_id}/account", response_model=UserOut, status_code=201)
def create_patient_account(
    patient_id: int,
    payload: PatientAccountCreate,
    db: Session = Depends(get_db),
    staff: User = Depends(require_staff),
):
    """A doctor sets up a login for a patient they registered (active immediately)."""
    patient = patient_for(staff, patient_id, db)
    if db.scalars(select(User).where(User.patient_id == patient_id)).first() is not None:
        raise HTTPException(409, "this patient already has a login account")
    email = payload.email.strip().lower()
    if db.scalars(select(User).where(User.email == email)).first() is not None:
        raise HTTPException(409, "an account with this email already exists")

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        name=patient.name,
        role="patient",
        status="active",
        patient_id=patient.id,
    )
    db.add(user)
    db.flush()
    audit.record(db, actor=staff.email, action="patient.account.create",
                 entity="user", entity_id=user.id,
                 detail={"patient_id": patient.id})
    db.commit()
    return user


@router.get("/{patient_id}/visits", response_model=list[VisitOut])
def list_visits(patient_id: int, db: Session = Depends(get_db), staff: User = Depends(require_staff)):
    patient_for(staff, patient_id, db)
    return list(db.scalars(
        select(Visit).where(Visit.patient_id == patient_id).order_by(Visit.id.desc())
    ))

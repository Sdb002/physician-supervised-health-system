from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db
from src.api.schemas import (
    PatientAccountCreate,
    PatientAccountOut,
    PatientCreate,
    PatientOut,
    PatientUpdate,
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
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    fields = payload.model_dump()
    fields["excluded_foods"] = _excluded_foods(payload.excluded_foods)
    patient = Patient(**fields)
    db.add(patient)
    db.flush()
    audit.record(db, actor="intake", action="patient.create", entity="patient", entity_id=patient.id)
    db.commit()
    return patient


@router.get("", response_model=list[PatientOut])
def list_patients(db: Session = Depends(get_db)):
    return list(db.scalars(select(Patient).order_by(Patient.id.desc())))


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(404, "patient not found")
    return patient


@router.patch("/{patient_id}", response_model=PatientOut)
def update_patient(
    patient_id: int,
    payload: PatientUpdate,
    db: Session = Depends(get_db),
    staff: User = Depends(get_current_user),
):
    """Change a patient's record. A plan still awaiting review was built from
    the old record, so it is rebuilt from the new one; approved and rejected
    assessments stay exactly as they were signed off."""
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(404, "patient not found")
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
        rebuilt.append(assessment.id)
    audit.record(db, actor=staff.email, action="patient.update", entity="patient",
                 entity_id=patient.id,
                 detail={"fields": sorted(changes), "assessments_rebuilt": rebuilt})
    db.commit()
    return patient


@router.get("/{patient_id}/account", response_model=PatientAccountOut)
def get_patient_account(patient_id: int, db: Session = Depends(get_db)):
    if db.get(Patient, patient_id) is None:
        raise HTTPException(404, "patient not found")
    user = db.scalars(select(User).where(User.patient_id == patient_id)).first()
    return PatientAccountOut(email=user.email if user else None)


@router.post("/{patient_id}/account", response_model=UserOut, status_code=201)
def create_patient_account(
    patient_id: int,
    payload: PatientAccountCreate,
    db: Session = Depends(get_db),
    staff: User = Depends(get_current_user),
):
    """A doctor sets up a login for a patient they registered (active immediately)."""
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(404, "patient not found")
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
def list_visits(patient_id: int, db: Session = Depends(get_db)):
    if db.get(Patient, patient_id) is None:
        raise HTTPException(404, "patient not found")
    return list(db.scalars(
        select(Visit).where(Visit.patient_id == patient_id).order_by(Visit.id.desc())
    ))

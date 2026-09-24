from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db
from src.api.schemas import (
    PatientAccountCreate,
    PatientAccountOut,
    PatientCreate,
    PatientOut,
    UserOut,
    VisitOut,
)
from src.core import audit
from src.core.security import hash_password
from src.db.models import Patient, User, Visit

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=PatientOut, status_code=201)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    patient = Patient(**payload.model_dump())
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

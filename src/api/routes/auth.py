"""Accounts and sessions.

Patients activate immediately (their account is linked to a new Patient row).
Doctors register as ``pending`` and cannot sign in until an admin approves
them via the /admin routes. Admins are provisioned at startup, never
self-registered.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db
from src.api.schemas import LoginIn, LoginOut, RegisterIn, UserOut
from src.core import audit
from src.core.rate_limit import login_allowed, record_login_failure, record_login_success
from src.core.security import create_token, hash_password, verify_password
from src.db.models import Patient, User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if db.scalars(select(User).where(User.email == email)).first() is not None:
        raise HTTPException(409, "an account with this email already exists")

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        name=payload.name.strip(),
        role=payload.role,
    )
    if payload.role == "doctor":
        user.status = "pending"
        user.specialty = payload.specialty.strip()
        user.license_no = payload.license_no.strip()
    else:
        if payload.profile is None:
            raise HTTPException(422, "patient registration requires a health profile")
        patient = Patient(
            name=payload.name.strip(),
            sex=payload.profile.sex,
            birth_year=payload.profile.birth_year,
            height_cm=payload.profile.height_cm,
            pregnant=payload.profile.pregnant,
            conditions=payload.profile.conditions,
            fitness_level=payload.profile.fitness_level,
            notes="self-registered account",
        )
        db.add(patient)
        db.flush()
        user.status = "active"
        user.patient_id = patient.id

    db.add(user)
    db.flush()
    audit.record(db, actor=email, action=f"user.register.{payload.role}",
                 entity="user", entity_id=user.id)
    db.commit()
    return user


@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if not login_allowed(email):
        raise HTTPException(429, "too many failed sign-in attempts — try again in a few minutes")

    user = db.scalars(select(User).where(User.email == email)).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        record_login_failure(email)
        raise HTTPException(401, "incorrect email or password")
    record_login_success(email)
    if user.status == "pending":
        raise HTTPException(
            403, "your registration is awaiting admin approval — try again later"
        )
    if user.status == "rejected":
        raise HTTPException(403, "your registration was declined by the admin")
    if payload.role is not None and user.role != payload.role:
        raise HTTPException(
            403,
            f"this is a {user.role} account — use the {user.role} sign-in page",
        )
    return LoginOut(token=create_token(user.id, user.role), user=user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user

"""Admin: approve/reject doctor registrations, platform stats, users, audit."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.api.deps import get_db, require_admin
from src.api.schemas import AdminPatientOut, AdminStats, AuditOut, DoctorDecision, UserOut
from src.core import audit
from src.db.models import Assessment, AuditLog, Patient, User, Visit

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStats)
def stats(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    def count(stmt):
        return db.scalar(select(func.count()).select_from(stmt.subquery()))

    return AdminStats(
        patients=count(select(Patient.id)),
        doctors_active=count(select(User.id).where(User.role == "doctor", User.status == "active")),
        doctors_pending=count(select(User.id).where(User.role == "doctor", User.status == "pending")),
        visits=count(select(Visit.id)),
        assessments_pending=count(select(Assessment.id).where(Assessment.status == "pending")),
        assessments_approved=count(select(Assessment.id).where(Assessment.status == "approved")),
        assessments_rejected=count(select(Assessment.id).where(Assessment.status == "rejected")),
    )


@router.get("/doctors", response_model=list[UserOut])
def list_doctors(
    status: str | None = Query(None, pattern="^(pending|active|rejected)$"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    stmt = select(User).where(User.role == "doctor")
    if status is not None:
        stmt = stmt.where(User.status == status)
    return list(db.scalars(stmt.order_by(User.id.desc())))


@router.post("/doctors/{user_id}/decision", response_model=UserOut)
def decide_doctor(
    user_id: int,
    payload: DoctorDecision,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    doctor = db.get(User, user_id)
    if doctor is None or doctor.role != "doctor":
        raise HTTPException(404, "doctor registration not found")
    if doctor.status != "pending":
        raise HTTPException(409, f"registration already {doctor.status}")

    doctor.status = "active" if payload.decision == "approved" else "rejected"
    audit.record(
        db,
        actor=admin.email,
        action=f"doctor.{payload.decision}",
        entity="user",
        entity_id=doctor.id,
        detail={"doctor_email": doctor.email, "license_no": doctor.license_no},
    )
    db.commit()
    return doctor


@router.get("/patients", response_model=list[AdminPatientOut])
def list_patients(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    emails = {
        u.patient_id: u.email
        for u in db.scalars(
            select(User).where(User.role == "patient", User.patient_id.is_not(None))
        )
    }
    return [
        AdminPatientOut(patient=p, account_email=emails.get(p.id))
        for p in db.scalars(select(Patient).order_by(Patient.id.desc()))
    ]


@router.get("/users", response_model=list[UserOut])
def list_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return list(db.scalars(select(User).order_by(User.id.desc())))


@router.get("/audit", response_model=list[AuditOut])
def recent_audit(
    limit: int = Query(25, ge=1, le=200),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return list(db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)))

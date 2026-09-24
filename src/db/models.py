"""ORM models: User, Patient, Visit, Assessment, Approval, AuditLog.

AuditLog rows are append-only: mapper-level guards below reject any UPDATE or
DELETE issued through the ORM, so the audit trail cannot be rewritten by
application code.
"""

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, String, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    """Login account. Doctors register as ``pending`` and can only sign in
    after an admin approves them; patient accounts link to a Patient row."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20))  # admin | doctor | patient
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | pending | rejected
    specialty: Mapped[str] = mapped_column(String(200), default="")
    license_no: Mapped[str] = mapped_column(String(100), default="")
    patient_id: Mapped[int | None] = mapped_column(ForeignKey("patients.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    patient: Mapped["Patient | None"] = relationship()


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    sex: Mapped[str] = mapped_column(String(10))  # "male" | "female"
    birth_year: Mapped[int]
    height_cm: Mapped[float]
    pregnant: Mapped[bool] = mapped_column(default=False)
    # physician-recorded condition keys, e.g. ["hypertension", "knee_osteoarthritis"]
    conditions: Mapped[list] = mapped_column(JSON, default=list)
    fitness_level: Mapped[str] = mapped_column(String(20), default="beginner")
    notes: Mapped[str] = mapped_column(String(2000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    visits: Mapped[list["Visit"]] = relationship(back_populates="patient", order_by="Visit.id")


class Visit(Base):
    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    weight_kg: Mapped[float]
    # physician-confirmed values, e.g. {"fasting_glucose": 110, "systolic_bp": 135, ...}
    biomarkers: Mapped[dict] = mapped_column(JSON, default=dict)
    # raw OCR output kept verbatim for audit; never used directly for scoring
    ocr_raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    patient: Mapped[Patient] = relationship(back_populates="visits")
    assessment: Mapped["Assessment | None"] = relationship(back_populates="visit", uselist=False)
    doctor_notes: Mapped[list["DoctorNote"]] = relationship(back_populates="visit", order_by="DoctorNote.id")


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    visit_id: Mapped[int] = mapped_column(ForeignKey("visits.id"), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | approved | rejected
    # full deterministic engine output: bmi, risk_flags, conditions, targets, plans
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    engine_version: Mapped[str] = mapped_column(String(20), default="0.1.0")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    visit: Mapped[Visit] = relationship(back_populates="assessment")
    approval: Mapped["Approval | None"] = relationship(back_populates="assessment", uselist=False)


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"), unique=True)
    physician_name: Mapped[str] = mapped_column(String(200))
    decision: Mapped[str] = mapped_column(String(20))  # approved | rejected
    # if the physician edited the engine output, the edited version they approved
    edited_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    comment: Mapped[str] = mapped_column(String(2000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    assessment: Mapped[Assessment] = relationship(back_populates="approval")


class DoctorNote(Base):
    """A physician's free-text note/recommendation on a visit, shown in the
    patient's report. Distinct from Approval.comment (a single remark tied to
    the approve/reject decision): notes may be added or edited at any time,
    including after approval."""

    __tablename__ = "doctor_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    visit_id: Mapped[int] = mapped_column(ForeignKey("visits.id"))
    physician_name: Mapped[str] = mapped_column(String(200))
    note: Mapped[str] = mapped_column(String(4000))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    # set only once the note has been edited after creation
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    visit: Mapped[Visit] = relationship(back_populates="doctor_notes")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(200))
    action: Mapped[str] = mapped_column(String(100))
    entity: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[int | None] = mapped_column(nullable=True)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


@event.listens_for(AuditLog, "before_update")
def _audit_no_update(mapper, connection, target):
    raise RuntimeError("AuditLog is append-only: updates are forbidden")


@event.listens_for(AuditLog, "before_delete")
def _audit_no_delete(mapper, connection, target):
    raise RuntimeError("AuditLog is append-only: deletes are forbidden")

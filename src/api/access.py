"""Whose patient a record is.

A patient belongs to one doctor (`patients.doctor_id`). A doctor reaches a
patient, and that patient's visits, assessments, notes and reports, only when
the patient is theirs. An admin oversees the service and reaches every record.
A patient who registered themselves has no doctor until one takes them on
(`POST /patients/{id}/claim`) or an admin assigns one.

Every staff route loads its record through here, so the rule lives in one
place. Another doctor's record answers 404, the same as one that does not
exist: a 403 would confirm that the patient is in the system.
"""

from fastapi import HTTPException
from sqlalchemy import Select
from sqlalchemy.orm import Session

from src.db.models import Assessment, Patient, User, Visit


def can_reach(user: User, patient: Patient) -> bool:
    """Whether a staff account may read or change this patient's records."""
    if user.role == "admin":
        return True
    return user.role == "doctor" and patient.doctor_id == user.id


def own_patients(query: Select, user: User) -> Select:
    """Narrow a query that selects from (or joins) patients to the ones this
    staff account may reach."""
    if user.role == "admin":
        return query
    return query.where(Patient.doctor_id == user.id)


def patient_for(user: User, patient_id: int, db: Session) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None or not can_reach(user, patient):
        raise HTTPException(404, "patient not found")
    return patient


def visit_for(user: User, visit_id: int, db: Session) -> Visit:
    visit = db.get(Visit, visit_id)
    if visit is None or not can_reach(user, visit.patient):
        raise HTTPException(404, "visit not found")
    return visit


def assessment_for(user: User, assessment_id: int, db: Session) -> Assessment:
    assessment = db.get(Assessment, assessment_id)
    if assessment is None or not can_reach(user, assessment.visit.patient):
        raise HTTPException(404, "assessment not found")
    return assessment

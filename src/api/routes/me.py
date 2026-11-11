"""Patient self-service: a patient sees their own visits and review status.

Report *content* stays behind the physician-approval gate in /report — this
route only exposes status, so a patient knows whether a report is ready.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api import daily_tasks
from src.api.deps import get_db, require_patient
from src.api.schemas import PatientDashboardOut, VisitStatusItem
from src.db.models import User, Visit

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/dashboard", response_model=PatientDashboardOut)
def my_dashboard(user: User = Depends(require_patient), db: Session = Depends(get_db)):
    if user.patient_id is None:
        raise HTTPException(404, "no patient profile is linked to this account")
    patient = user.patient
    visits = db.scalars(
        select(Visit).where(Visit.patient_id == patient.id).order_by(Visit.id.desc())
    )
    items = []
    for visit in visits:
        assessment = visit.assessment
        status = assessment.status if assessment else "pending"
        items.append(
            VisitStatusItem(
                visit=visit,
                status=status,
                assessment_id=assessment.id if assessment else None,
                report_ready=status == "approved",
            )
        )
    return PatientDashboardOut(patient=patient, items=items)


def _patient_id(user: User) -> int:
    if user.patient_id is None:
        raise HTTPException(404, "no patient profile is linked to this account")
    return user.patient_id


@router.get("/tasks")
def my_tasks(user: User = Depends(require_patient), db: Session = Depends(get_db)):
    """Today's tasks from the approved plan (meals and exercise), which are
    ticked, and the streak of complete days (src/api/daily_tasks.py)."""
    return daily_tasks.today_view(db, _patient_id(user))


class TaskTick(BaseModel):
    done: bool


@router.put("/tasks/{key}")
def tick_task(key: str, payload: TaskTick, user: User = Depends(require_patient),
              db: Session = Depends(get_db)):
    """Tick or untick one of today's tasks; only today's can be changed."""
    try:
        return daily_tasks.set_done(db, _patient_id(user), key, payload.done)
    except daily_tasks.UnknownTaskError:
        raise HTTPException(404, f"'{key}' is not one of today's tasks")

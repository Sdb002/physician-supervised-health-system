"""Physician review: the human gate between engine output and any report."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.deps import get_db, require_staff
from src.api.schemas import ApprovalOut, PlanEditIn, QueueItem, ReviewDecision
from src.api.services import allowed_foods_for, recompute_edited_result
from src.core import audit
from src.db.models import Approval, Assessment, User

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/queue", response_model=list[QueueItem])
def review_queue(db: Session = Depends(get_db)):
    pending = db.scalars(
        select(Assessment).where(Assessment.status == "pending").order_by(Assessment.id)
    )
    return [
        QueueItem(assessment=a, patient=a.visit.patient, visit=a.visit)
        for a in pending
    ]


@router.get("/{assessment_id}", response_model=QueueItem)
def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(404, "assessment not found")
    return QueueItem(assessment=assessment, patient=assessment.visit.patient,
                     visit=assessment.visit)


@router.get("/{assessment_id}/foods")
def list_allowed_foods(assessment_id: int, db: Session = Depends(get_db)):
    """Live, contraindication-filtered food list for the plan editor."""
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(404, "assessment not found")
    return allowed_foods_for(assessment.result)


@router.post("/{assessment_id}/recompute")
def recompute_plan(assessment_id: int, payload: PlanEditIn, db: Session = Depends(get_db)):
    """Preview a physician-edited diet/exercise plan with all derived numbers
    (kcal, totals, coverage, weekly volume) recomputed deterministically.
    Returns the full edited result to pass as ``edited_result`` on approval."""
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(404, "assessment not found")
    if assessment.status != "pending":
        raise HTTPException(409, f"assessment already {assessment.status}")
    try:
        return recompute_edited_result(
            assessment.result, assessment.visit.weight_kg, payload
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@router.post("/{assessment_id}/decision", response_model=ApprovalOut, status_code=201)
def decide(
    assessment_id: int,
    payload: ReviewDecision,
    staff: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(404, "assessment not found")
    if assessment.status != "pending":
        raise HTTPException(409, f"assessment already {assessment.status}")

    approval = Approval(
        assessment_id=assessment.id,
        # the approver of record is the authenticated account, never client
        # input — otherwise any signed-in doctor could approve under someone
        # else's name and the approval gate would attest to nothing
        physician_name=staff.name,
        decision=payload.decision,
        comment=payload.comment,
        edited_result=payload.edited_result,
    )
    assessment.status = payload.decision
    db.add(approval)
    db.flush()

    audit.record(
        db,
        actor=staff.email,
        action=f"assessment.{payload.decision}",
        entity="assessment",
        entity_id=assessment.id,
        detail={
            "comment": payload.comment,
            "edited": payload.edited_result is not None,
        },
    )
    db.commit()
    return approval

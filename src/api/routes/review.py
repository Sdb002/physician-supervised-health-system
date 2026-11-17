"""Physician review: the human gate between engine output and any report."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api import report_wording
from src.api.access import assessment_for, own_patients
from src.api.deps import get_db, require_staff
from src.api.schemas import (
    ApprovalOut,
    PlanEditIn,
    QueueItem,
    ReviewDecision,
    WordingIn,
    WordingOut,
)
from src.api.services import allowed_foods_for, recompute_edited_result
from src.core import audit
from src.db.models import Approval, Assessment, Patient, User, Visit
from src.llm.client import llm_available

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/queue", response_model=list[QueueItem])
def review_queue(db: Session = Depends(get_db), staff: User = Depends(require_staff)):
    """Assessments waiting for a decision: a doctor's own patients' only."""
    pending = db.scalars(
        own_patients(select(Assessment).join(Visit).join(Patient), staff)
        .where(Assessment.status == "pending").order_by(Assessment.id)
    )
    return [
        QueueItem(assessment=a, patient=a.visit.patient, visit=a.visit)
        for a in pending
    ]


@router.get("/{assessment_id}", response_model=QueueItem)
def get_assessment(
    assessment_id: int, db: Session = Depends(get_db), staff: User = Depends(require_staff)
):
    assessment = assessment_for(staff, assessment_id, db)
    return QueueItem(assessment=assessment, patient=assessment.visit.patient,
                     visit=assessment.visit)


@router.get("/{assessment_id}/foods")
def list_allowed_foods(
    assessment_id: int, db: Session = Depends(get_db), staff: User = Depends(require_staff)
):
    """Live, contraindication-filtered food list for the plan editor."""
    assessment = assessment_for(staff, assessment_id, db)
    return allowed_foods_for(assessment.result)


@router.post("/{assessment_id}/recompute")
def recompute_plan(
    assessment_id: int,
    payload: PlanEditIn,
    db: Session = Depends(get_db),
    staff: User = Depends(require_staff),
):
    """Preview a physician-edited diet/exercise plan with all derived numbers
    (kcal, totals, coverage, weekly volume) recomputed deterministically.
    Returns the full edited result to pass as ``edited_result`` on approval."""
    assessment = assessment_for(staff, assessment_id, db)
    if assessment.status != "pending":
        raise HTTPException(409, f"assessment already {assessment.status}")
    try:
        return recompute_edited_result(
            assessment.result, assessment.visit.weight_kg, payload
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@router.post("/{assessment_id}/wording", response_model=WordingOut)
def word_report(
    assessment_id: int,
    payload: WordingIn,
    db: Session = Depends(get_db),
    staff: User = Depends(require_staff),
):
    """Write the patient's report, in both languages, from the plan as the
    physician has it (edits and comment included), for them to read before
    approving. This is the only place a report is worded: an approval names
    the wording returned here and releases exactly that text. Asking again
    for an unchanged plan returns the same wording."""
    assessment = assessment_for(staff, assessment_id, db)
    if assessment.status != "pending":
        raise HTTPException(409, f"assessment already {assessment.status}")

    draft = report_wording.prepare(
        assessment.report_draft, assessment.visit.patient.name,
        payload.edited_result or assessment.result, payload.comment,
        use_llm=payload.use_llm, prepared_by=staff.email,
    )
    if draft is not assessment.report_draft:
        assessment.report_draft = draft
        audit.record(db, actor=staff.email, action="assessment.report_worded",
                     entity="assessment", entity_id=assessment.id,
                     detail=report_wording.provenance(draft))
        db.commit()
    return WordingOut(fingerprint=draft["fingerprint"], texts=draft["texts"],
                      ai_available=llm_available())


@router.post("/{assessment_id}/decision", response_model=ApprovalOut, status_code=201)
def decide(
    assessment_id: int,
    payload: ReviewDecision,
    staff: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    assessment = assessment_for(staff, assessment_id, db)
    if assessment.status != "pending":
        raise HTTPException(409, f"assessment already {assessment.status}")

    # an approval releases the report wording the physician was shown, and
    # only that: it must name the wording, and the wording must have been
    # written from the plan, comment and patient name now being approved
    released, detail = None, {}
    if payload.decision == "approved":
        try:
            released = report_wording.approved(
                assessment.report_draft, payload.wording, assessment.visit.patient.name,
                payload.edited_result or assessment.result, payload.comment,
            )
        except report_wording.WordingError as exc:
            raise HTTPException(409, str(exc))
        detail["report"] = report_wording.provenance(assessment.report_draft)

    approval = Approval(
        assessment_id=assessment.id,
        # the approver of record is the authenticated account, never client
        # input — otherwise any signed-in doctor could approve under someone
        # else's name and the approval gate would attest to nothing
        physician_name=staff.name,
        decision=payload.decision,
        comment=payload.comment,
        edited_result=payload.edited_result,
        report_text=released,
    )
    assessment.status = payload.decision
    assessment.report_draft = None  # decided: the approval holds what was released
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
            **detail,
        },
    )
    db.commit()
    return approval

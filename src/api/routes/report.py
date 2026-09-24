"""Patient report — HARD-GATED: 403 until a physician Approval row exists.

The text is phrased by the LLM when configured (and requested), otherwise by
the deterministic template. Either way the content comes exclusively from the
approved assessment (the physician's edited version, if they edited it).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db
from src.api.report_template import template_report
from src.api.schemas import ReportOut
from src.db.models import User, Visit
from src.llm.client import LLMNotConfiguredError, LLMRefusedError, llm_available

router = APIRouter(prefix="/report", tags=["report"])


@router.get("/{visit_id}", response_model=ReportOut)
def get_report(
    visit_id: int,
    lang: str = Query("en", pattern="^(en|bn)$"),
    use_llm: bool = Query(True, description="Phrase with the LLM when configured"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    visit = db.get(Visit, visit_id)
    if visit is None:
        raise HTTPException(404, "visit not found")

    # patients may only read reports for their own visits; staff see all
    if user.role == "patient" and visit.patient_id != user.patient_id:
        raise HTTPException(403, "you can only view your own reports")

    assessment = visit.assessment
    approval = assessment.approval if assessment else None
    if approval is None or approval.decision != "approved":
        raise HTTPException(
            403,
            "report unavailable: this visit's assessment has not been approved "
            "by a physician",
        )

    result = approval.edited_result or assessment.result
    patient_name = visit.patient.name

    source = "template"
    text = None
    if use_llm and llm_available():
        from src.llm.report_writer import write_report

        try:
            text = write_report(patient_name, result, lang)
            source = "llm"
        except (LLMNotConfiguredError, LLMRefusedError):
            text = None
    if text is None:
        text = template_report(patient_name, result, lang, comment=approval.comment)

    return ReportOut(
        visit_id=visit.id,
        patient_name=patient_name,
        lang=lang,
        source=source,
        text=text,
        approved_by=approval.physician_name,
        approved_at=approval.created_at,
        comment=approval.comment,
        visit_date=visit.created_at,
        result=result,
        notes=list(visit.doctor_notes),
    )

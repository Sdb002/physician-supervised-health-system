"""Patient report — HARD-GATED: 403 until a physician Approval row exists.

The text is the wording the physician was shown and approved, stored with the
approval (src/api/report_wording.py). This route writes none: it does not
phrase, it does not call an LLM and it imports no LLM code, so every reader
of a report gets the sentences the physician approved. The content comes
exclusively from the approved assessment (the physician's edited version, if
they edited it).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.access import can_reach
from src.api.deps import get_current_user, get_db
from src.api.report_template import for_patient, template_report
from src.api.schemas import ReportOut
from src.api.services import ENGINE_VERSION
from src.db.models import User, Visit

router = APIRouter(prefix="/report", tags=["report"])


@router.get("/{visit_id}", response_model=ReportOut)
def get_report(
    visit_id: int,
    lang: str = Query("en", pattern="^(en|bn)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    visit = db.get(Visit, visit_id)
    if visit is None:
        raise HTTPException(404, "visit not found")

    # a patient reads the reports of their own visits; a doctor, those of
    # their own patients; an admin, any (src/api/access.py)
    if user.role == "patient":
        if visit.patient_id != user.patient_id:
            raise HTTPException(403, "you can only view your own reports")
    elif not can_reach(user, visit.patient):
        raise HTTPException(404, "visit not found")

    assessment = visit.assessment
    approval = assessment.approval if assessment else None
    if approval is None or approval.decision != "approved":
        raise HTTPException(
            403,
            "report unavailable: this visit's assessment has not been approved "
            "by a physician",
        )

    result = approval.edited_result or assessment.result
    shown = for_patient(result)
    patient_name = visit.patient.name

    wording = (approval.report_text or {}).get(lang)
    if wording:
        text, source = wording["text"], wording["source"]
    else:
        # approved before the wording was kept with the approval: the
        # standard wording, which is worked out from the approved plan alone
        text = template_report(patient_name, shown, lang, comment=approval.comment)
        source = "template"

    return ReportOut(
        visit_id=visit.id,
        patient_name=patient_name,
        lang=lang,
        source=source,
        text=text,
        approved_by=approval.physician_name,
        approved_at=approval.created_at,
        engine_version=assessment.engine_version,
        current_engine_version=ENGINE_VERSION,
        comment=approval.comment,
        visit_date=visit.created_at,
        result=shown if user.role == "patient" else result,
        notes=list(visit.doctor_notes),
    )

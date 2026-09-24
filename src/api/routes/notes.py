"""Doctor's notes/recommendations on a visit — free text a physician can add
or edit at any time (including after approval), surfaced in the patient's
report. Access is mixed like /report: staff manage freely, patients may only
read their own, and only once the visit's assessment is approved."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db, require_staff
from src.api.schemas import DoctorNoteCreate, DoctorNoteOut, DoctorNoteUpdate
from src.core import audit
from src.db.models import DoctorNote, User, Visit, utcnow

router = APIRouter(prefix="/visits/{visit_id}/notes", tags=["notes"])


def _visit_for_read(visit_id: int, user: User, db: Session) -> Visit:
    visit = db.get(Visit, visit_id)
    if visit is None:
        raise HTTPException(404, "visit not found")
    if user.role == "patient":
        if visit.patient_id != user.patient_id:
            raise HTTPException(403, "you can only view your own notes")
        approval = visit.assessment.approval if visit.assessment else None
        if approval is None or approval.decision != "approved":
            raise HTTPException(403, "notes are unavailable until a physician approves this visit")
    return visit


@router.get("", response_model=list[DoctorNoteOut])
def list_notes(visit_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    visit = _visit_for_read(visit_id, user, db)
    return list(visit.doctor_notes)


@router.post("", response_model=DoctorNoteOut, status_code=201)
def create_note(
    visit_id: int,
    payload: DoctorNoteCreate,
    staff: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    if db.get(Visit, visit_id) is None:
        raise HTTPException(404, "visit not found")
    # attributed to the authenticated account, not client input — see review.py
    note = DoctorNote(visit_id=visit_id, physician_name=staff.name, note=payload.note)
    db.add(note)
    db.flush()
    audit.record(db, actor=staff.email, action="note.created", entity="visit_note",
                 entity_id=note.id, detail={"visit_id": visit_id})
    db.commit()
    return note


@router.patch("/{note_id}", response_model=DoctorNoteOut)
def update_note(
    visit_id: int,
    note_id: int,
    payload: DoctorNoteUpdate,
    staff: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    note = db.get(DoctorNote, note_id)
    if note is None or note.visit_id != visit_id:
        raise HTTPException(404, "note not found")
    note.note = payload.note
    note.updated_at = utcnow()
    audit.record(db, actor=staff.email, action="note.edited", entity="visit_note",
                 entity_id=note.id, detail={"visit_id": visit_id})
    db.commit()
    db.refresh(note)
    return note

"""Per-visit intake: manual biomarker entry (+ optional OCR prefill).

Creating a visit immediately runs the deterministic assessment engine and
stores a pending Assessment for physician review. OCR only prefills the form —
the physician-confirmed values in the request body are what get scored.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.api.deps import get_db
from src.api.schemas import AssessmentOut, BiomarkersIn, OcrResult, VisitCreate
from src.api.services import ENGINE_VERSION, build_assessment
from src.core import audit
from src.db.models import Assessment, Patient, Visit
from src.llm.client import LLMNotConfiguredError, LLMRefusedError

router = APIRouter(tags=["intake"])

_ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
_MAX_OCR_BYTES = 8 * 1024 * 1024  # generous for a phone photo of a lab report

# first bytes of each declared type, so a client can't send an oversized or
# arbitrary payload under a spoofed image Content-Type
_SIGNATURES: dict[str, tuple[bytes, ...]] = {
    "image/png": (b"\x89PNG",),
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/gif": (b"GIF87a", b"GIF89a"),
    "image/webp": (b"RIFF",),  # full check also needs bytes 8-12 == b"WEBP"
}


def _matches_declared_type(data: bytes, content_type: str) -> bool:
    if content_type == "image/webp":
        return data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    return any(data.startswith(sig) for sig in _SIGNATURES.get(content_type, ()))


@router.post("/patients/{patient_id}/visits", response_model=AssessmentOut, status_code=201)
def create_visit(patient_id: int, payload: VisitCreate, db: Session = Depends(get_db)):
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(404, "patient not found")

    biomarkers = {k: v for k, v in payload.biomarkers.model_dump().items() if v is not None}
    visit = Visit(
        patient_id=patient.id,
        weight_kg=payload.weight_kg,
        biomarkers=biomarkers,
        ocr_raw=payload.ocr_raw,
    )
    db.add(visit)
    db.flush()

    result = build_assessment(patient, visit)
    assessment = Assessment(visit_id=visit.id, result=result, engine_version=ENGINE_VERSION)
    db.add(assessment)
    db.flush()

    audit.record(db, actor="intake", action="visit.create", entity="visit", entity_id=visit.id,
                 detail={"biomarkers": biomarkers})
    audit.record(db, actor="engine", action="assessment.create", entity="assessment",
                 entity_id=assessment.id, detail={"engine_version": ENGINE_VERSION})
    db.commit()
    return assessment


@router.post("/intake/ocr", response_model=OcrResult)
async def ocr_lab_report(file: UploadFile = File(...)):
    """Extract biomarker values from a lab-report image, to PREFILL the intake
    form. Values must still be confirmed by the physician before submission."""
    if file.content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(415, f"unsupported image type: {file.content_type}")

    from src.llm.ocr_extract import extract_biomarkers

    image_bytes = await file.read(_MAX_OCR_BYTES + 1)
    if len(image_bytes) > _MAX_OCR_BYTES:
        raise HTTPException(413, "image too large (max 8 MB)")
    if not _matches_declared_type(image_bytes, file.content_type):
        raise HTTPException(415, "file content doesn't match its declared image type")
    try:
        extracted = extract_biomarkers(image_bytes, file.content_type)
    except LLMNotConfiguredError as e:
        raise HTTPException(503, str(e))
    except LLMRefusedError as e:
        raise HTTPException(422, str(e))

    return OcrResult(
        biomarkers=BiomarkersIn(
            fasting_glucose=extracted.fasting_glucose,
            systolic_bp=extracted.systolic_bp,
            diastolic_bp=extracted.diastolic_bp,
            hemoglobin=extracted.hemoglobin,
        ),
        notes=extracted.notes,
    )

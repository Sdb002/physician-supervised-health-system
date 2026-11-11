"""Per-visit intake: manual biomarker entry (+ optional OCR prefill).

Creating a visit immediately runs the deterministic assessment engine and
stores a pending Assessment for physician review. OCR only prefills the form —
the physician-confirmed values in the request body are what get scored.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from src.api.deps import get_db
from src.api.schemas import AssessmentOut, BiomarkersIn, OcrResult, VisitCreate
from src.api.services import ENGINE_VERSION, build_assessment
from src.core import audit
from src.core.config import settings
from src.db.models import Assessment, Patient, Visit
from src.llm.client import LLMNotConfiguredError, LLMRefusedError, llm_available
from src.ocr.engine import OcrEngineUnavailableError, UnreadableImageError, local_available

router = APIRouter(tags=["intake"])

_ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
_PDF = "application/pdf"
_MAX_OCR_BYTES = 8 * 1024 * 1024  # generous for a phone photo or a lab's PDF report

# first bytes of each declared type, so a client can't send an oversized or
# arbitrary payload under a spoofed image Content-Type
_SIGNATURES: dict[str, tuple[bytes, ...]] = {
    "image/png": (b"\x89PNG",),
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/gif": (b"GIF87a", b"GIF89a"),
    _PDF: (b"%PDF-",),
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


def available_ocr_reader() -> str | None:
    """"local" or "claude": the reader OCR_ENGINE picks among those this
    server has, or None when there is none."""
    choice = settings.ocr_engine.strip().lower()
    if choice in ("auto", "local") and local_available():
        return "local"
    if choice in ("auto", "claude") and llm_available():
        return "claude"
    return None


def _ocr_reader() -> str:
    """available_ocr_reader(), or a 503 saying what is missing."""
    choice = settings.ocr_engine.strip().lower()
    if choice not in ("auto", "local", "claude"):
        raise HTTPException(503, f"OCR_ENGINE must be auto, local or claude, not {choice!r}")
    reader = available_ocr_reader()
    if reader is not None:
        return reader
    if choice == "local":
        raise HTTPException(503, "The local lab-slip reader is not installed on this server "
                                 "(pip install rapidocr onnxruntime).")
    if choice == "claude":
        raise HTTPException(503, "OCR_ENGINE is claude but ANTHROPIC_API_KEY is not set.")
    raise HTTPException(503, "No lab-slip reader is set up on this server: install the local "
                             "reader (pip install rapidocr onnxruntime) or set ANTHROPIC_API_KEY.")


def _read_locally(data: bytes, content_type: str) -> OcrResult:
    from src.ocr.engine import ENGINE_NAME, PDF_TEXT_NAME, read_lines, read_pdf_lines
    from src.ocr.lab_report import parse_lab_report

    engine = ENGINE_NAME
    if content_type == _PDF:
        lines, scanned = read_pdf_lines(data)
        if not scanned:
            engine = PDF_TEXT_NAME
    else:
        lines = read_lines(data)
    reading = parse_lab_report(lines)
    return OcrResult(
        biomarkers=BiomarkersIn(
            fasting_glucose=reading.fasting_glucose,
            systolic_bp=reading.systolic_bp,
            diastolic_bp=reading.diastolic_bp,
            hemoglobin=reading.hemoglobin,
        ),
        notes=" ".join(reading.notes),
        engine=engine,
        text=[line.text for line in lines],
    )


def _read_with_claude(image_bytes: bytes, content_type: str) -> OcrResult:
    from src.llm.ocr_extract import extract_biomarkers

    extracted = extract_biomarkers(image_bytes, content_type)
    return OcrResult(
        biomarkers=BiomarkersIn(
            fasting_glucose=extracted.fasting_glucose,
            systolic_bp=extracted.systolic_bp,
            diastolic_bp=extracted.diastolic_bp,
            hemoglobin=extracted.hemoglobin,
        ),
        notes=extracted.notes,
        engine="Claude",
    )


@router.post("/intake/ocr", response_model=OcrResult)
async def ocr_lab_report(file: UploadFile = File(...)):
    """Extract biomarker values from a lab-report photo or PDF, to PREFILL
    the intake form. Values must still be confirmed by the physician before
    submission. A photo is read on this server by RapidOCR, or by Claude
    (see OCR_ENGINE); a PDF is always read on this server - a lab's PDF
    carries its text, which is taken as printed."""
    if file.content_type not in _ALLOWED_IMAGE_TYPES | {_PDF}:
        raise HTTPException(415, f"unsupported file type: {file.content_type}")

    image_bytes = await file.read(_MAX_OCR_BYTES + 1)
    if len(image_bytes) > _MAX_OCR_BYTES:
        raise HTTPException(413, "file too large (max 8 MB)")
    if not _matches_declared_type(image_bytes, file.content_type):
        raise HTTPException(415, "file content doesn't match its declared type")

    reader = "local" if file.content_type == _PDF else _ocr_reader()
    try:
        # both readers are CPU- or network-bound and synchronous: keep them
        # off the event loop
        if reader == "local":
            return await run_in_threadpool(_read_locally, image_bytes, file.content_type)
        return await run_in_threadpool(_read_with_claude, image_bytes, file.content_type)
    except UnreadableImageError as e:
        raise HTTPException(415, str(e))
    except (LLMNotConfiguredError, OcrEngineUnavailableError) as e:
        raise HTTPException(503, str(e))
    except LLMRefusedError as e:
        raise HTTPException(422, str(e))

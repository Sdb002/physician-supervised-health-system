from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BiomarkersIn(BaseModel):
    fasting_glucose: float | None = Field(None, ge=10, le=1000, description="mg/dL")
    systolic_bp: float | None = Field(None, ge=40, le=300, description="mmHg")
    diastolic_bp: float | None = Field(None, ge=20, le=200, description="mmHg")
    hemoglobin: float | None = Field(None, ge=1, le=25, description="g/dL")


class PatientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    sex: str = Field(pattern="^(male|female)$")
    birth_year: int = Field(ge=1900, le=2030)
    height_cm: float = Field(gt=30, lt=260)
    pregnant: bool = False
    conditions: list[str] = []
    fitness_level: str = Field("beginner", pattern="^(beginner|intermediate|advanced)$")
    notes: str = ""


class PatientOut(PatientCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class VisitCreate(BaseModel):
    weight_kg: float = Field(gt=2, lt=400)
    biomarkers: BiomarkersIn = BiomarkersIn()
    ocr_raw: dict | None = None  # raw OCR output kept for audit, if OCR was used


class VisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    patient_id: int
    weight_kg: float
    biomarkers: dict
    created_at: datetime


class AssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    visit_id: int
    status: str
    result: dict
    engine_version: str
    created_at: datetime


class QueueItem(BaseModel):
    assessment: AssessmentOut
    patient: PatientOut
    visit: VisitOut


class MealItemEdit(BaseModel):
    food_id: str = Field(min_length=1, max_length=50)
    qty_g: float = Field(ge=5, le=2000)
    # display name the physician saw — lets the server detect when the dataset
    # was replaced and the id now denotes a different food entirely
    name_en: str = Field("", max_length=200)


class ExercisePlanEdit(BaseModel):
    aerobic_days: int = Field(ge=1, le=7)
    strength_days: int = Field(ge=0, le=7)
    flexibility_days: int = Field(ge=0, le=7)
    aerobic_min_per_session: int = Field(ge=5, le=180)
    # category -> exercise_ids the physician kept (validated against the
    # contraindication-filtered exercise list server-side)
    type: dict[str, list[str]] = {}


class PlanEditIn(BaseModel):
    """Physician edits to the diet/exercise plan, recomputed deterministically."""

    meals: dict[str, list[MealItemEdit]]
    exercise: ExercisePlanEdit | None = None


class ReviewDecision(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")
    comment: str = ""
    edited_result: dict | None = None  # if the physician edited the engine output


class ApprovalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    assessment_id: int
    physician_name: str
    decision: str
    comment: str
    created_at: datetime


class DoctorNoteCreate(BaseModel):
    note: str = Field(min_length=1, max_length=4000)


class DoctorNoteUpdate(BaseModel):
    note: str = Field(min_length=1, max_length=4000)


class DoctorNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    visit_id: int
    physician_name: str
    note: str
    created_at: datetime
    updated_at: datetime | None


class ReportOut(BaseModel):
    visit_id: int
    patient_name: str
    lang: str
    source: str  # "llm" | "template"
    text: str
    approved_by: str
    approved_at: datetime
    # structured payload so the dashboard can render a full report document;
    # `result` is the approved (possibly physician-edited) assessment
    comment: str = ""
    visit_date: datetime | None = None
    result: dict = {}
    notes: list[DoctorNoteOut] = []


class OcrResult(BaseModel):
    biomarkers: BiomarkersIn
    notes: str = ""


# --- auth / accounts ---------------------------------------------------------

_EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class PatientProfileIn(BaseModel):
    """Health profile a patient supplies when registering their own account."""

    sex: str = Field(pattern="^(male|female)$")
    birth_year: int = Field(ge=1900, le=2030)
    height_cm: float = Field(gt=30, lt=260)
    pregnant: bool = False
    conditions: list[str] = []
    fitness_level: str = Field("beginner", pattern="^(beginner|intermediate|advanced)$")


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(pattern=_EMAIL_PATTERN, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(pattern="^(doctor|patient)$")  # admins are provisioned, never self-registered
    # doctor-only
    specialty: str = Field("", max_length=200)
    license_no: str = Field("", max_length=100)
    # patient-only
    profile: PatientProfileIn | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    name: str
    role: str
    status: str
    specialty: str
    license_no: str
    patient_id: int | None
    created_at: datetime


class LoginIn(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(max_length=128)
    # when set, the login is rejected if the account has a different role —
    # each dashboard has its own sign-in page
    role: str | None = Field(None, pattern="^(admin|doctor|patient)$")


class LoginOut(BaseModel):
    token: str
    user: UserOut


class PatientAccountCreate(BaseModel):
    """Login credentials a doctor sets up for an existing patient."""

    email: str = Field(pattern=_EMAIL_PATTERN, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class PatientAccountOut(BaseModel):
    """Whether a patient row has a linked login, and which email."""

    email: str | None


class DoctorDecision(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")


class AdminPatientOut(BaseModel):
    """Patient row for the admin panel, with the linked login (if any)."""

    patient: PatientOut
    account_email: str | None


class AdminStats(BaseModel):
    patients: int
    doctors_active: int
    doctors_pending: int
    visits: int
    assessments_pending: int
    assessments_approved: int
    assessments_rejected: int


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    actor: str
    action: str
    entity: str
    entity_id: int | None
    detail: dict
    created_at: datetime


class VisitStatusItem(BaseModel):
    """One row of the patient dashboard: a visit plus where it is in review."""

    visit: VisitOut
    status: str  # pending | approved | rejected
    assessment_id: int | None
    report_ready: bool


class PatientDashboardOut(BaseModel):
    patient: PatientOut
    items: list[VisitStatusItem]

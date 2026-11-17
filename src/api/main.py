from contextlib import asynccontextmanager
import logging
import os
import re

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.deps import require_staff
from src.api.routes import admin, auth, foods, intake, me, notes, patients, report, review
from src.core.config import settings
from src.core.logging import setup_logging
from src.core.security import hash_password
from src.db.session import SessionLocal, init_db
from src.llm.client import llm_available


def ensure_default_admin() -> None:
    """Create the bootstrap admin account if no admin exists yet."""
    from sqlalchemy import select

    from src.db.models import User

    with SessionLocal() as db:
        exists = db.scalars(select(User).where(User.role == "admin")).first()
        if exists is not None:
            return
        db.add(
            User(
                email=settings.admin_email.lower(),
                password_hash=hash_password(settings.admin_password),
                name=settings.admin_name,
                role="admin",
                status="active",
            )
        )
        db.commit()
        logging.getLogger(__name__).info(
            "created default admin account %s (change ADMIN_PASSWORD in .env)",
            settings.admin_email,
        )


def check_published_defaults(config=settings) -> None:
    """Refuse to start a deployment on the auth settings published in the
    README: with the default SECRET_KEY anyone can forge a session token, and
    the default admin password is an admin login. On a developer's machine
    they only earn a warning."""
    defaults = config.published_defaults()
    if not defaults:
        return
    names = " and ".join(defaults)
    if config.is_local:
        logging.getLogger(__name__).warning(
            "%s still at the published default — fine on this machine, never "
            "for a deployment. Set your own in .env.", names,
        )
        return
    raise RuntimeError(
        f"refusing to start: {names} still at the value published in the README, "
        "and this is not a local development setup (ENVIRONMENT, DATABASE_URL or "
        "CORS_ORIGINS says so). Set your own in .env."
    )


def check_hosted_database(config=settings) -> None:
    """On Vercel the disk is read-only and forgets everything between
    requests: a SQLite file there (the default when DATABASE_URL is not set)
    would fail on the first write or lose every record. Say so plainly
    instead of failing obscurely on every request."""
    if os.environ.get("VERCEL") and config.database_url.startswith("sqlite"):
        raise RuntimeError(
            "refusing to start: DATABASE_URL is not set, and a SQLite file cannot keep data "
            "on Vercel. Add a Postgres database to the project (Storage, then Neon), which "
            "sets DATABASE_URL, and redeploy."
        )


def seed_demo_data() -> None:
    """The synthetic demo patients and logins, for a hosted demo whose
    database starts empty (SEED_DEMO_DATA). Seeded once; when two instances
    start together, the one that loses the race leaves it to the other."""
    from sqlalchemy.exc import IntegrityError

    from src.db.demo import seed_demo

    log = logging.getLogger(__name__)
    with SessionLocal() as db:
        try:
            if seed_demo(db, actor="startup", report=log.info):
                log.info("seeded the synthetic demo patients (SEED_DEMO_DATA)")
        except IntegrityError:
            db.rollback()
            log.info("demo data already being seeded by another instance")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    try:
        check_hosted_database()
        check_published_defaults()
        init_db()
        ensure_default_admin()
        if settings.seed_demo_data:
            seed_demo_data()
    except Exception as exc:
        if not os.environ.get("VERCEL"):
            raise  # a local run stops right there, with the traceback
        # On Vercel a failed start-up only showed as FUNCTION_INVOCATION_FAILED
        # on every request, the reason buried in the runtime log: keep the
        # instance up and answer every request with the reason instead.
        logging.getLogger(__name__).exception("start-up failed")
        global STARTUP_ERROR
        STARTUP_ERROR = startup_failure(exc)
    yield


# why this instance could not start, when it could not (on Vercel only)
STARTUP_ERROR: str | None = None

_CREDENTIALS_IN_URL = re.compile(r"(://[^:/@\s]+):[^@\s]+@")


def startup_failure(exc: Exception) -> str:
    """What a failed start-up is answered with. The refusals above are
    written by this app and name settings, never their values; anything else
    is reported by its type and first line, with any password in a database
    URL taken out."""
    if isinstance(exc, RuntimeError) and str(exc).startswith("refusing to start"):
        return str(exc)
    first_line = (str(exc).strip().splitlines() or [""])[0][:300]
    redacted = _CREDENTIALS_IN_URL.sub(r"\1:***@", first_line)
    return f"{type(exc).__name__}: {redacted}"


app = FastAPI(
    title="Physician-Supervised Health System",
    description=(
        "Deterministic clinical engine + physician approval gate. "
        "LLM is used only for lab-report OCR and report phrasing."
    ),
    version="0.1.0",
    lifespan=lifespan,
    # "/api" when the API shares a domain with the dashboard: on Vercel, where
    # vercel.json routes /api/* here with the prefix kept. Paths without the
    # prefix still route, so a local run is unaffected either way.
    root_path=settings.api_root_path or ("/api" if os.environ.get("VERCEL") else ""),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers(request, call_next):
    if STARTUP_ERROR is not None:
        response = JSONResponse(
            {"detail": f"The API could not start: {STARTUP_ERROR}"}, status_code=503)
    else:
        response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(me.router)
# food and dish names only, and the sign-up form needs them before any account exists
app.include_router(foods.router)
# clinical workflow routes are staff-only (doctor or admin); the report route
# manages its own access because patients may fetch their own approved reports
app.include_router(patients.router, dependencies=[Depends(require_staff)])
app.include_router(intake.router, dependencies=[Depends(require_staff)])
app.include_router(review.router, dependencies=[Depends(require_staff)])
app.include_router(report.router)
# doctor's-note routes manage their own access, same reasoning as /report
app.include_router(notes.router)


@app.get("/health", tags=["meta"])
def health():
    reader = intake.available_ocr_reader()
    return {
        "status": "ok",
        "llm_configured": llm_available(),
        # who reads a lab slip on this server: "RapidOCR" (locally), "Claude", or null
        "ocr_reader": {"local": "RapidOCR", "claude": "Claude"}.get(reader),
    }

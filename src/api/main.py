from contextlib import asynccontextmanager
import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.deps import require_staff
from src.api.routes import admin, auth, intake, me, notes, patients, report, review
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    check_published_defaults()
    init_db()
    ensure_default_admin()
    yield


app = FastAPI(
    title="Physician-Supervised Health System",
    description=(
        "Deterministic clinical engine + physician approval gate. "
        "LLM is used only for lab-report OCR and report phrasing."
    ),
    version="0.1.0",
    lifespan=lifespan,
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
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(me.router)
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
    return {"status": "ok", "llm_configured": llm_available()}

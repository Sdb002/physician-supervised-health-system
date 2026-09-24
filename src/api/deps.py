from collections.abc import Generator

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.core.security import decode_token
from src.db.models import User
from src.db.session import SessionLocal

_bearer = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(401, "not authenticated — sign in first")
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(401, "session expired or invalid — please sign in again")
    user = db.get(User, payload.get("uid"))
    if user is None or user.status != "active":
        raise HTTPException(401, "account not found or no longer active")
    return user


def require_roles(*roles: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, f"this action requires role: {' or '.join(roles)}")
        return user

    return dependency


require_staff = require_roles("doctor", "admin")
require_admin = require_roles("admin")
require_patient = require_roles("patient")

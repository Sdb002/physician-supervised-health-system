"""Append-only audit trail: who did what, to which entity, when.

Writing goes through `record()` only. Immutability is enforced at the mapper
level in src/db/models.py — ORM updates/deletes on AuditLog raise.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import AuditLog


def record(
    session: Session,
    actor: str,
    action: str,
    entity: str,
    entity_id: int | None = None,
    detail: dict | None = None,
) -> AuditLog:
    row = AuditLog(
        actor=actor,
        action=action,
        entity=entity,
        entity_id=entity_id,
        detail=detail or {},
    )
    session.add(row)
    return row


def trail(session: Session, entity: str | None = None, entity_id: int | None = None) -> list[AuditLog]:
    q = select(AuditLog).order_by(AuditLog.id)
    if entity is not None:
        q = q.where(AuditLog.entity == entity)
    if entity_id is not None:
        q = q.where(AuditLog.entity_id == entity_id)
    return list(session.scalars(q))

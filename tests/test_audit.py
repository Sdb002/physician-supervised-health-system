"""Audit trail: writes are recorded; updates and deletes are impossible."""

import pytest

from src.core import audit


def test_record_and_trail(db_session):
    audit.record(db_session, actor="Dr. Rahman", action="assessment.approved",
                 entity="assessment", entity_id=1, detail={"comment": "ok"})
    db_session.commit()
    rows = audit.trail(db_session, entity="assessment", entity_id=1)
    assert len(rows) == 1
    assert rows[0].actor == "Dr. Rahman"
    assert rows[0].detail == {"comment": "ok"}


def test_audit_rows_cannot_be_updated(db_session):
    row = audit.record(db_session, actor="a", action="x", entity="e")
    db_session.commit()
    row.actor = "tampered"
    with pytest.raises(RuntimeError, match="append-only"):
        db_session.commit()
    db_session.rollback()


def test_audit_rows_cannot_be_deleted(db_session):
    row = audit.record(db_session, actor="a", action="x", entity="e")
    db_session.commit()
    db_session.delete(row)
    with pytest.raises(RuntimeError, match="append-only"):
        db_session.commit()
    db_session.rollback()

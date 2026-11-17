"""Patient: the doctor whose patient this is.

Revision ID: 0005
Revises: 0004

Until now any doctor could open any patient. `patients.doctor_id` links a
patient to one doctor, and the API shows a doctor only their own.

Existing patients have no recorded doctor, so the link is read off the audit
log where it can be: the doctor who first approved or rejected one of the
patient's assessments, failing that the doctor who first edited the record.
A patient no doctor has acted on stays unassigned (NULL) for a doctor to take
on or an admin to assign; nobody is guessed.
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

_FROM_DECISIONS = """
UPDATE patients SET doctor_id = (
    SELECT u.id FROM audit_log a
    JOIN assessments s ON s.id = a.entity_id
    JOIN visits v ON v.id = s.visit_id
    JOIN users u ON u.email = a.actor AND u.role = 'doctor'
    WHERE a.entity = 'assessment'
      AND a.action IN ('assessment.approved', 'assessment.rejected')
      AND v.patient_id = patients.id
    ORDER BY a.id LIMIT 1
) WHERE doctor_id IS NULL
"""

_FROM_RECORD_EDITS = """
UPDATE patients SET doctor_id = (
    SELECT u.id FROM audit_log a
    JOIN users u ON u.email = a.actor AND u.role = 'doctor'
    WHERE a.entity = 'patient' AND a.action = 'patient.update'
      AND a.entity_id = patients.id
    ORDER BY a.id LIMIT 1
) WHERE doctor_id IS NULL
"""


def upgrade() -> None:
    with op.batch_alter_table("patients") as batch:
        batch.add_column(sa.Column("doctor_id", sa.Integer, nullable=True))
        batch.create_foreign_key("fk_patients_doctor_id", "users", ["doctor_id"], ["id"])
        batch.create_index("ix_patients_doctor_id", ["doctor_id"])
    op.execute(_FROM_DECISIONS)
    op.execute(_FROM_RECORD_EDITS)


def downgrade() -> None:
    with op.batch_alter_table("patients") as batch:
        batch.drop_index("ix_patients_doctor_id")
        batch.drop_constraint("fk_patients_doctor_id", type_="foreignkey")
        batch.drop_column("doctor_id")

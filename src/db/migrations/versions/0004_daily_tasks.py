"""Daily task list: what a patient ticked off each day.

Revision ID: 0004
Revises: 0003

One row per patient per day: the day's tasks the patient marked done (its
meals, its exercise groups), how many tasks the day had and whether all were
done - the streak counts complete days.
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "daily_task_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("patient_id", sa.Integer, sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("day", sa.Date, nullable=False),
        sa.Column("visit_id", sa.Integer, sa.ForeignKey("visits.id"), nullable=False),
        sa.Column("done", sa.JSON, nullable=False),
        sa.Column("total", sa.Integer, nullable=False),
        sa.Column("complete", sa.Boolean, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("patient_id", "day"),
    )
    op.create_index("ix_daily_task_logs_patient_id", "daily_task_logs", ["patient_id"])


def downgrade() -> None:
    op.drop_index("ix_daily_task_logs_patient_id", table_name="daily_task_logs")
    op.drop_table("daily_task_logs")

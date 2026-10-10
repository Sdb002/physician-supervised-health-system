"""Baseline: the schema as it stood when migrations were introduced.

Revision ID: 0001
Revises:

Databases made before this by Base.metadata.create_all() already hold these
tables and carry no alembic_version row, so each table is created only if it
is missing: the same upgrade serves a new database and adopts an old one.
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    existing = set(sa.inspect(op.get_bind()).get_table_names())

    if "patients" not in existing:
        op.create_table(
            "patients",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("sex", sa.String(10), nullable=False),
            sa.Column("birth_year", sa.Integer, nullable=False),
            sa.Column("height_cm", sa.Float, nullable=False),
            sa.Column("pregnant", sa.Boolean, nullable=False),
            sa.Column("conditions", sa.JSON, nullable=False),
            sa.Column("fitness_level", sa.String(20), nullable=False),
            sa.Column("notes", sa.String(2000), nullable=False),
            sa.Column("created_at", sa.DateTime, nullable=False),
        )
    if "audit_log" not in existing:
        op.create_table(
            "audit_log",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("actor", sa.String(200), nullable=False),
            sa.Column("action", sa.String(100), nullable=False),
            sa.Column("entity", sa.String(50), nullable=False),
            sa.Column("entity_id", sa.Integer, nullable=True),
            sa.Column("detail", sa.JSON, nullable=False),
            sa.Column("created_at", sa.DateTime, nullable=False),
        )
    if "users" not in existing:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("email", sa.String(255), nullable=False),
            sa.Column("password_hash", sa.String(255), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("role", sa.String(20), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("specialty", sa.String(200), nullable=False),
            sa.Column("license_no", sa.String(100), nullable=False),
            sa.Column("patient_id", sa.Integer, sa.ForeignKey("patients.id"), nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=True)
    if "visits" not in existing:
        op.create_table(
            "visits",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("patient_id", sa.Integer, sa.ForeignKey("patients.id"), nullable=False),
            sa.Column("weight_kg", sa.Float, nullable=False),
            sa.Column("biomarkers", sa.JSON, nullable=False),
            sa.Column("ocr_raw", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False),
        )
    if "assessments" not in existing:
        op.create_table(
            "assessments",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("visit_id", sa.Integer, sa.ForeignKey("visits.id"), nullable=False,
                      unique=True),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("result", sa.JSON, nullable=False),
            sa.Column("engine_version", sa.String(20), nullable=False),
            sa.Column("created_at", sa.DateTime, nullable=False),
        )
    if "doctor_notes" not in existing:
        op.create_table(
            "doctor_notes",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("visit_id", sa.Integer, sa.ForeignKey("visits.id"), nullable=False),
            sa.Column("physician_name", sa.String(200), nullable=False),
            sa.Column("note", sa.String(4000), nullable=False),
            sa.Column("created_at", sa.DateTime, nullable=False),
            sa.Column("updated_at", sa.DateTime, nullable=True),
        )
    if "approvals" not in existing:
        op.create_table(
            "approvals",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("assessment_id", sa.Integer, sa.ForeignKey("assessments.id"),
                      nullable=False, unique=True),
            sa.Column("physician_name", sa.String(200), nullable=False),
            sa.Column("decision", sa.String(20), nullable=False),
            sa.Column("edited_result", sa.JSON, nullable=True),
            sa.Column("comment", sa.String(2000), nullable=False),
            sa.Column("created_at", sa.DateTime, nullable=False),
        )


def downgrade() -> None:
    raise NotImplementedError("the baseline is not reversible: it would drop every table")

"""Patient profile: trimester, dietary restrictions, activity level.

Revision ID: 0002
Revises: 0001

What engine 0.7.0 reads off the patient: the trimester sets the extra energy
in pregnancy, the dietary restrictions go through the food gate, and the
activity level replaces the one the energy target used to assume.
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("patients") as batch:
        batch.add_column(sa.Column("pregnancy_trimester", sa.Integer, nullable=True))
        batch.add_column(sa.Column("dietary_restrictions", sa.JSON, nullable=False,
                                   server_default="[]"))
        batch.add_column(sa.Column("activity_level", sa.String(20), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("patients") as batch:
        batch.drop_column("activity_level")
        batch.drop_column("dietary_restrictions")
        batch.drop_column("pregnancy_trimester")

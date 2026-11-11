"""Patient: the foods and dishes they do not eat.

Revision ID: 0003
Revises: 0002

What engine 0.11.0 reads off the patient beside the dietary restrictions: a
list of single foods and dishes, picked from the food table and the recipe
list, that go through the food gate for this patient only.
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("patients") as batch:
        batch.add_column(sa.Column("excluded_foods", sa.JSON, nullable=False,
                                   server_default="[]"))


def downgrade() -> None:
    with op.batch_alter_table("patients") as batch:
        batch.drop_column("excluded_foods")

"""Report wording: written before approval, kept with it.

Revision ID: 0006
Revises: 0005

Until now the report's text was written each time a report was opened, after
the approval, so a patient could read wording (the LLM's, when one was
configured) that the approving physician had never seen. The wording is now
prepared for the physician to read before approving and stored with the
approval:

- `assessments.report_draft`: the wording as last prepared for the reviewing
  physician, with what it was written from;
- `approvals.report_text`: the wording that was approved, per language. The
  report route serves this and never writes any.

Approvals made before this have no stored wording (NULL). Their reports show
the deterministic standard wording, as they did wherever no LLM was
configured; no LLM is asked.
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("assessments") as batch:
        batch.add_column(sa.Column("report_draft", sa.JSON, nullable=True))
    with op.batch_alter_table("approvals") as batch:
        batch.add_column(sa.Column("report_text", sa.JSON, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("approvals") as batch:
        batch.drop_column("report_text")
    with op.batch_alter_table("assessments") as batch:
        batch.drop_column("report_draft")

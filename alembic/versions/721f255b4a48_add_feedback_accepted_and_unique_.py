"""add feedback accepted and unique workflow constraint

Revision ID: 721f255b4a48
Revises: c0dc3bde94ba
Create Date: 2026-08-13 12:32:27.030504

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "721f255b4a48"
down_revision: str | Sequence[str] | None = "c0dc3bde94ba"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "feedback",
        sa.Column(
            "accepted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.alter_column(
        "feedback",
        "accepted",
        server_default=None,
    )

    op.create_unique_constraint(
        "uq_feedback_workflow_id",
        "feedback",
        ["workflow_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "uq_feedback_workflow_id",
        "feedback",
        type_="unique",
    )

    op.drop_column("feedback", "accepted")

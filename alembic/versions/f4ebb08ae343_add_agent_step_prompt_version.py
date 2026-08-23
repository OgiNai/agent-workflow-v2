"""add agent step prompt version

Revision ID: f4ebb08ae343
Revises: 721f255b4a48
Create Date: 2026-08-21 19:53:16.805258

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f4ebb08ae343"
down_revision: str | Sequence[str] | None = "721f255b4a48"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agent_steps",
        sa.Column(
            "prompt_version",
            sa.String(length=50),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "agent_steps",
        "prompt_version",
    )

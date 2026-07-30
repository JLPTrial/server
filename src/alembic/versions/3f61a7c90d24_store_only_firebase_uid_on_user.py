"""store only firebase uid on user

Revision ID: 3f61a7c90d24
Revises: aa46b7d17339
Create Date: 2026-07-11 21:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3f61a7c90d24"
down_revision: str | None = "aa46b7d17339"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("email")
        batch_op.drop_column("name")


def downgrade() -> None:
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("email", sqlmodel.sql.sqltypes.AutoString(), nullable=False)
        )
        batch_op.add_column(
            sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False)
        )
        batch_op.create_unique_constraint("uq_user_email", ["email"])

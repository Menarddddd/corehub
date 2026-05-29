"""set departments updated_at default and backfill nulls

Revision ID: f39c365e49d6
Revises:
Create Date: 2026-05-29 13:33:35.336902

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f39c365e49d6"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "departments",
        "updated_at",
        server_default=sa.func.now(),
        existing_type=sa.DateTime(timezone=True),
    )

    op.execute("UPDATE departments SET updated_at = NOW() WHERE updated_at IS NULL")


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "departments",
        "updated_at",
        server_default=None,
        existing_type=sa.DateTime(timezone=True),
    )

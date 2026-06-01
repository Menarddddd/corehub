"""created conversation, conversation_members and updated messages models

Revision ID: 4ede810667ce
Revises: ca8e67425111
Create Date: 2026-06-01 14:20:45.754369

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "4ede810667ce"
down_revision: Union[str, Sequence[str], None] = "ca8e67425111"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column(
            "is_group", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("created_by_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "conversation_members",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "is_admin", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "conversation_id", "user_id", name="uq_conversation_member"
        ),
    )

    # IMPORTANT: nullable=True first if table already has rows
    op.add_column("messages", sa.Column("conversation_id", sa.UUID(), nullable=True))

    op.alter_column("messages", "sender_id", existing_type=sa.UUID(), nullable=True)

    op.alter_column(
        "messages",
        "content",
        existing_type=sa.VARCHAR(length=500),
        type_=sa.Text(),
        existing_nullable=False,
    )

    # Recreate sender FK if you want SET NULL
    op.drop_constraint("messages_sender_id_fkey", "messages", type_="foreignkey")
    op.create_foreign_key(
        "messages_sender_id_fkey",
        "messages",
        "users",
        ["sender_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.drop_constraint("messages_receiver_id_fkey", "messages", type_="foreignkey")

    op.create_foreign_key(
        "messages_conversation_id_fkey",
        "messages",
        "conversations",
        ["conversation_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_column("messages", "receiver_id")
    op.drop_column("messages", "is_read")
    # ### end Alembic commands ###


def downgrade() -> None:
    op.add_column(
        "messages",
        sa.Column(
            "is_read", sa.BOOLEAN(), server_default=sa.text("false"), nullable=False
        ),
    )
    op.add_column(
        "messages",
        sa.Column("receiver_id", sa.UUID(), nullable=False),
    )

    op.drop_constraint("messages_conversation_id_fkey", "messages", type_="foreignkey")

    op.create_foreign_key(
        "messages_receiver_id_fkey",
        "messages",
        "users",
        ["receiver_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Optional: restore old sender FK behavior if needed
    op.drop_constraint("messages_sender_id_fkey", "messages", type_="foreignkey")
    op.create_foreign_key(
        "messages_sender_id_fkey",
        "messages",
        "users",
        ["sender_id"],
        ["id"],
    )

    op.alter_column(
        "messages",
        "content",
        existing_type=sa.Text(),
        type_=sa.VARCHAR(length=500),
        existing_nullable=False,
    )

    op.alter_column("messages", "sender_id", existing_type=sa.UUID(), nullable=False)

    op.drop_column("messages", "conversation_id")
    op.drop_table("conversation_members")
    op.drop_table("conversations")
    # ### end Alembic commands ###

import uuid
import sqlalchemy as sa
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.users import User


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )
    receiver_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )
    content: Mapped[str] = mapped_column(sa.String(500), nullable=False)
    is_read: Mapped[bool] = mapped_column(
        sa.Boolean, default=None, server_default=sa.text("false"), nullable=False
    )
    sent_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    # RELATIONSHIP
    sender: Mapped["User | None"] = relationship(
        back_populates="sent_messages", foreign_keys=[sender_id]
    )
    receiver: Mapped["User | None"] = relationship(
        back_populates="received_messages", foreign_keys=[receiver_id]
    )

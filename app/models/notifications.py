import uuid
import sqlalchemy as sa
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.users import User


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    title: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    body: Mapped[str] = mapped_column(sa.Text, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), default=None, nullable=True
    )
    sent_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    # RELATIONSHIP
    user: Mapped["User"] = relationship(back_populates="notifications")

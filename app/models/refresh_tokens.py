import uuid
import sqlalchemy as sa
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.users import User


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    hashed_token: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    user_agent: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    revoked: Mapped[bool] = mapped_column(
        sa.Boolean, default=False, server_default=sa.text("false"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    # RELATIONSHIP
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

import uuid
import sqlalchemy as sa
from typing import TYPE_CHECKING
from datetime import date, datetime
from sqlalchemy import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.users import User


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    priority: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    due_date: Mapped[date] = mapped_column(sa.Date(), nullable=False)
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
    assigned_to: Mapped["User | None"] = relationship(
        back_populates="assigned_tasks",
        foreign_keys="Task.assigned_to_id",
    )
    created_by: Mapped["User | None"] = relationship(
        back_populates="created_tasks",
        foreign_keys="Task.created_by_id",
    )

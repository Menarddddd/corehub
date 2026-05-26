import uuid
import sqlalchemy as sa
from typing import TYPE_CHECKING
from datetime import datetime
from enum import Enum
from sqlalchemy import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.departments import Department
    from app.models.tasks import Task
    from app.models.messages import Message
    from app.models.notifications import Notification
    from app.models.announcements import Announcement


class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    first_name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    username: Mapped[str] = mapped_column(sa.String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(sa.String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    role: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    profile: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
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

    # RELATIONSHIPS
    department: Mapped["Department | None"] = relationship(back_populates="users")
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="user", cascade="save-update", passive_deletes="all"
    )
    sent_messages: Mapped[list["Message"]] = relationship(
        back_populates="sender",
        foreign_keys="Message.sender_id",
        cascade="save-update",
        passive_deletes="all",
    )
    received_messages: Mapped[list["Message"]] = relationship(
        back_populates="receiver",
        foreign_keys="Message.receiver_id",
        cascade="save-update",
        passive_deletes="all",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    announcements: Mapped[list["Announcement"]] = relationship(
        back_populates="posted_by", cascade="save-update", passive_deletes="all"
    )

    # TABLE CONSTRAINTS
    __table_args__ = (
        sa.CheckConstraint("length(username) >= 7", name="ck_username_check"),
        sa.CheckConstraint("length(email) >= 7", name="ck_email_check"),
    )

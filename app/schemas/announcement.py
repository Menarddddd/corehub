from datetime import datetime, timedelta, timezone
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.schemas.cursor import CursorPageInfo
from app.schemas.enum import AnnouncementPriority


class AnnouncementBase(BaseModel):
    title: str = Field(max_length=100)
    body: str = Field(min_length=1)
    priority: AnnouncementPriority


class AnnouncementCreate(AnnouncementBase):
    expires_at: datetime

    @field_validator("expires_at")
    @classmethod
    def check_set_date(cls, value: datetime):
        tomorrow = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)

        if value < tomorrow:
            raise ValueError("expires_at must be set to at least tomorrow")
        return value


class AnnouncementResponse(AnnouncementBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None = None
    expires_at: datetime
    created_at: datetime
    updated_at: datetime


class AnnouncementUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=100)
    body: str | None = None
    priority: AnnouncementPriority | None = None
    expires_at: datetime | None = None

    @field_validator("expires_at", mode="before")
    @classmethod
    def check_set_date(cls, value: datetime):
        if value is None:
            return value

        tomorrow = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)

        if value < tomorrow:
            raise ValueError("expires_at must be set to at least tomorrow")
        return value


class AnnouncementPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[AnnouncementResponse]
    page_info: CursorPageInfo

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.cursor import CursorPageInfo
from app.schemas.enum import NotificationType


class NotificationBase(BaseModel):
    user_id: UUID
    type: NotificationType
    title: str = Field(min_length=1, max_length=150)
    body: str = Field(min_length=1)


class NotificationCreate(NotificationBase):
    pass


class NotificationResponse(NotificationBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    read_at: datetime | None
    sent_at: datetime


class NotificationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    read_at: datetime


class NotificationPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[NotificationResponse]
    page_info: CursorPageInfo

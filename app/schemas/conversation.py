# app/schemas/conversation.py
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.cursor import CursorPageInfo


# Message Schemas
class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    sender_id: UUID | None = None
    content: str
    sent_at: datetime
    updated_at: datetime


class MessagePageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[MessageResponse]
    page_info: CursorPageInfo


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=1000)


# Member Schemas
class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    is_admin: bool
    joined_at: datetime


# Conversation Schemas
class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str | None = None
    is_group: bool
    created_by_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class ConversationInboxItem(BaseModel):
    """
    Represents one item in the inbox list.
    Shows conversation info + last message preview.
    """

    conversation_id: UUID
    name: str | None = None  # Group name or other person's name
    is_group: bool
    last_message: str | None = None
    last_message_at: datetime | None = None
    unread_count: int = 0


class ConversationInboxResponse(BaseModel):
    items: list[ConversationInboxItem]
    page_info: CursorPageInfo


# Create Schemas
class CreateDMRequest(BaseModel):
    """Create a direct message conversation with one person."""

    user_id: UUID


class CreateGroupRequest(BaseModel):
    """Create a group conversation with multiple people."""

    name: str = Field(min_length=1, max_length=100)
    member_ids: list[UUID] = Field(min_length=1)


class AddMemberRequest(BaseModel):
    user_id: UUID


class UpdateGroupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=100)

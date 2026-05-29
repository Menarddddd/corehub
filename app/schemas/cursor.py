from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class CursorPageInfo(BaseModel):
    has_next: bool
    next_cursor: str | None = None


class CursorPayload(BaseModel):
    item_id: UUID
    created_at: datetime | None = None

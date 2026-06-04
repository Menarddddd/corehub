from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.user import UserResponse

class TaskSummary(BaseModel):
    total: int
    pending: int
    in_progress: int
    completed: int
    cancelled: int


class RecentAnnouncement(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    body: str
    priority: str
    expires_at: datetime
    created_at: datetime



class DashboardResponse(BaseModel):
    user: UserResponse
    tasks: TaskSummary
    unread_notifications: int
    unread_messages: int
    recent_announcements: list[RecentAnnouncement]
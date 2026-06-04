import asyncio

from app.models.users import User
from app.repositories.dashboard import DashboardRepository
from app.schemas.dashboard import (
    DashboardResponse,
    RecentAnnouncement,
    TaskSummary,
)
from app.schemas.user import UserResponse


class DashboardService:
    def __init__(self, repo: DashboardRepository):
        self.repo = repo

    async def get_dashboard(self, current_user: User) -> DashboardResponse:
        """
        Build the dashboard response for the current user.
        All queries run concurrently using asyncio.gather.
        """
        (
            task_counts,
            unread_notifications,
            unread_messages,
            announcements,
        ) = await asyncio.gather(
            self.repo.get_task_counts(current_user.id),
            self.repo.get_unread_notification_count(current_user.id),
            self.repo.get_unread_message_count(current_user.id),
            self.repo.get_recent_announcements(),
        )

        return DashboardResponse(
            user=UserResponse.model_validate(current_user),
            tasks=TaskSummary(**task_counts),
            unread_notifications=unread_notifications,
            unread_messages=unread_messages,
            recent_announcements=[
                RecentAnnouncement.model_validate(a)
                for a in announcements
            ],
        )
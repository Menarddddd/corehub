# app/services/notification.py
from uuid import UUID
from datetime import datetime, timezone

from app.core.exceptions import FieldNotFoundException, ForbiddenException
from app.models.notifications import Notification
from app.models.users import User
from app.repositories.notification import NotificationRepository
from app.schemas.cursor import CursorPageInfo
from app.schemas.notification import (
    NotificationPageResponse,
    NotificationResponse,
)
from app.utils.cursor import get_cursor_info


class NotificationService:
    def __init__(self, repo: NotificationRepository):
        self.repo = repo

    async def get_notifications_service(
        self, user_id: UUID, limit: int, cursor: str | None
    ) -> NotificationPageResponse:
        """
        Fetch all notifications for the current user
        ordered by most recent first.
        """
        notifications = await self.repo.get_notifications(
            Notification.user_id == user_id,
            limit=limit,
            cursor=cursor,
        )
        notifications, has_next, next_cursor = get_cursor_info(notifications, limit)

        return NotificationPageResponse(
            items=[
                NotificationResponse.model_validate(notification)
                for notification in notifications
            ],
            page_info=CursorPageInfo(has_next=has_next, next_cursor=next_cursor),
        )

    async def get_unread_notifications_service(
        self, user_id: UUID, limit: int, cursor: str | None
    ) -> NotificationPageResponse:
        """
        Fetch only unread notifications for the current user.
        Unread means read_at is NULL.
        """
        notifications = await self.repo.get_notifications(
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
            limit=limit,
            cursor=cursor,
        )
        notifications, has_next, next_cursor = get_cursor_info(notifications, limit)

        return NotificationPageResponse(
            items=[
                NotificationResponse.model_validate(notification)
                for notification in notifications
            ],
            page_info=CursorPageInfo(has_next=has_next, next_cursor=next_cursor),
        )

    async def mark_as_read_service(self, notification: Notification) -> Notification:
        """
        Mark a single notification as read by setting read_at to now.
        """
        notification.read_at = datetime.now(timezone.utc)
        return await self.repo.update(notification)

    async def mark_all_as_read_service(self, user_id: UUID) -> None:
        """
        Mark all unread notifications as read for the current user.
        Only updates notifications where read_at is still NULL.
        """
        await self.repo.mark_all_as_read(user_id)

    async def delete_notification_service(self, notification: Notification) -> None:
        """
        Delete a single notification.
        """
        await self.repo.delete(notification)

import redis.asyncio as aioredis
from uuid import UUID
from datetime import datetime, timezone

from app.models.notifications import Notification
from app.repositories.notification import NotificationRepository
from app.schemas.cursor import CursorPageInfo
from app.schemas.notification import (
    NotificationPageResponse,
    NotificationResponse,
)
from app.utils.cursor import get_cursor_info


class NotificationService:
    def __init__(self, repo: NotificationRepository, redis: aioredis.Redis):
        self.repo = repo
        self.redis = redis

    async def _build_cache_key(
        self, user_id: UUID, limit: int, cursor: str | None
    ) -> str:
        c = cursor if cursor else "none"
        return f"notification:user:{user_id}:limit:{limit}:cursor:{c}"

    async def _invalidate_notifications_cache(self):
        "Delete all cached tasks"
        async for key in self.redis.scan_iter(match="notification:*"):
            await self.redis.delete(key)

    async def get_notifications_service(
        self, user_id: UUID, limit: int, cursor: str | None
    ) -> NotificationPageResponse:
        """
        Fetch all notifications for the current user
        ordered by most recent first.
        """
        cache_key = await self._build_cache_key(user_id, limit, cursor)
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return NotificationPageResponse.model_validate_json(cached_data)

        notifications = await self.repo.get_notifications(
            Notification.user_id == user_id,
            limit=limit,
            cursor=cursor,
        )
        notifications, has_next, next_cursor = get_cursor_info(notifications, limit)

        response = NotificationPageResponse(
            items=[
                NotificationResponse.model_validate(notification)
                for notification in notifications
            ],
            page_info=CursorPageInfo(has_next=has_next, next_cursor=next_cursor),
        )

        await self.redis.set(
            cache_key,
            response.model_dump_json(),
            ex=180,
        )

        return response

    async def get_unread_notifications_service(
        self, user_id: UUID, limit: int, cursor: str | None
    ) -> NotificationPageResponse:
        """
        Fetch only unread notifications for the current user.
        Unread means read_at is NULL.
        """
        cache_key = await self._build_cache_key(user_id, limit, cursor)
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return NotificationPageResponse.model_validate_json(cached_data)

        notifications = await self.repo.get_notifications(
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
            limit=limit,
            cursor=cursor,
        )
        notifications, has_next, next_cursor = get_cursor_info(notifications, limit)

        response = NotificationPageResponse(
            items=[
                NotificationResponse.model_validate(notification)
                for notification in notifications
            ],
            page_info=CursorPageInfo(has_next=has_next, next_cursor=next_cursor),
        )

        await self.redis.set(
            cache_key,
            response.model_dump_json(),
            ex=180,
        )

        return response

    async def mark_as_read_service(self, notification: Notification) -> Notification:
        """
        Mark a single notification as read by setting read_at to now.
        """
        notification.read_at = datetime.now(timezone.utc)
        response = await self.repo.update(notification)
        await self._invalidate_notifications_cache()
        return response

    async def mark_all_as_read_service(self, user_id: UUID) -> None:
        """
        Mark all unread notifications as read for the current user.
        Only updates notifications where read_at is still NULL.
        """
        await self.repo.mark_all_as_read(user_id)
        await self._invalidate_notifications_cache()

    async def delete_notification_service(self, notification: Notification) -> None:
        """
        Delete a single notification.
        """
        await self.repo.delete(notification)
        await self._invalidate_notifications_cache()

from uuid import UUID
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notifications import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Notification)

    async def get_notifications(
        self,
        *conditions,
        limit: int,
        cursor: str | None = None,
        options: list | None = None,
    ) -> Sequence[Notification]:
        """
        Fetch notifications with cursor-based pagination.
        Ordered by sent_at descending (newest first).
        """
        return await self.get_many(
            *conditions, limit=limit, cursor=cursor, options=options
        )

    async def mark_all_as_read(self, user_id: UUID) -> None:
        """
        Bulk update all unread notifications for a user.
        More efficient than loading each one individually.
        """
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
            .values(read_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)
        await self.db.commit()

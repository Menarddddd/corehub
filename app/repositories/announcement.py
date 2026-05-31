from typing import Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.announcements import Announcement
from app.repositories.base import BaseRepository


class AnnouncementRepository(BaseRepository[Announcement]):

    def __init__(self, db: AsyncSession):
        super().__init__(db, Announcement)

    async def get_announcements(
        self, *conditions, limit: int, cursor: str | None, options: list | None = None
    ) -> Sequence[Announcement]:
        return await self.get_many(
            *conditions, limit=limit, cursor=cursor, options=options
        )
